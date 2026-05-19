from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lg_mode_tools import lg_mode_cartesian, make_square_grid, normalize_field, inner_product, write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Derive why p=1 dominates under axisymmetric mismatch and when l-mixing appears."
    )
    parser.add_argument("--l-list", type=str, default="0,4,8")
    parser.add_argument("--eta-list", type=str, default="0.98,0.95,0.90")
    parser.add_argument("--p-max", type=int, default=6)
    parser.add_argument("--l-span", type=int, default=3)
    parser.add_argument("--grid-size", type=int, default=512)
    parser.add_argument("--extent", type=float, default=8.0)
    parser.add_argument("--shift-list", type=str, default="0.05,0.10,0.20")
    parser.add_argument("--tilt-list", type=str, default="0.10,0.20,0.40")
    parser.add_argument("--zoff-list", type=str, default="0.10,0.25,0.50")
    parser.add_argument("--output-prefix", type=str, default="radial_order_lmix_")
    return parser.parse_args()


def parse_float_list(text: str) -> list[float]:
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def parse_int_list(text: str) -> list[int]:
    return [int(item.strip()) for item in text.split(",") if item.strip()]


def radial_mismatch_power(l: int, p: int, eta: float) -> float:
    l_abs = abs(l)
    s = (1.0 - eta * eta) / (1.0 + eta * eta)
    c0 = (2.0 * eta / (1.0 + eta * eta)) ** (2 * (l_abs + 1))
    return math.comb(p + l_abs, p) * c0 * (s * s) ** p


def small_mismatch_parameter(eta: float) -> float:
    return abs((1.0 - eta * eta) / (1.0 + eta * eta))


def build_radial_rows(l_values: list[int], eta_values: list[float], p_max: int) -> list[dict]:
    rows: list[dict] = []
    for l in l_values:
        for eta in eta_values:
            total = 0.0
            for p in range(p_max + 1):
                power = radial_mismatch_power(l, p, eta)
                total += power
                rows.append(
                    {
                        "family": "axisymmetric_size_mismatch",
                        "l": l,
                        "eta": eta,
                        "p": p,
                        "power": power,
                        "small_parameter_s_abs": small_mismatch_parameter(eta),
                    }
                )
            rows.append(
                {
                    "family": "axisymmetric_size_mismatch",
                    "l": l,
                    "eta": eta,
                    "p": "partial_sum_0_to_pmax",
                    "power": total,
                    "small_parameter_s_abs": small_mismatch_parameter(eta),
                }
            )
    return rows


def build_basis(
    x: np.ndarray,
    y: np.ndarray,
    dx: float,
    l_target: int,
    l_span: int,
    p_max: int,
) -> dict[tuple[int, int], np.ndarray]:
    cache: dict[tuple[int, int], np.ndarray] = {}
    for l in range(max(0, l_target - l_span), l_target + l_span + 1):
        for p in range(p_max + 1):
            cache[(p, l)] = normalize_field(lg_mode_cartesian(x, y, p=p, l=l, w0=1.0), dx)
    return cache


def modal_weights(
    field: np.ndarray,
    basis: dict[tuple[int, int], np.ndarray],
    dx: float,
) -> dict[tuple[int, int], float]:
    normalized = normalize_field(field, dx)
    out: dict[tuple[int, int], float] = {}
    for key, mode in basis.items():
        coeff = inner_product(mode, normalized, dx)
        out[key] = float(abs(coeff) ** 2)
    return out


def summarize_weights(weights: dict[tuple[int, int], float]) -> tuple[dict[int, float], dict[int, float]]:
    by_l: dict[int, float] = {}
    by_p: dict[int, float] = {}
    for (p, l), value in weights.items():
        by_l[l] = by_l.get(l, 0.0) + value
        by_p[p] = by_p.get(p, 0.0) + value
    return by_l, by_p


def build_lmix_rows(
    l_values: list[int],
    p_max: int,
    l_span: int,
    grid_size: int,
    extent: float,
    shift_values: list[float],
    tilt_values: list[float],
    zoff_values: list[float],
) -> list[dict]:
    rows: list[dict] = []
    x, y, dx = make_square_grid(extent=extent, grid_size=grid_size)

    for l_target in l_values:
        basis = build_basis(x, y, dx, l_target=l_target, l_span=l_span, p_max=p_max)
        base = normalize_field(lg_mode_cartesian(x, y, p=0, l=l_target, w0=1.0), dx)

        for z_norm in zoff_values:
            field = normalize_field(lg_mode_cartesian(x, y, p=0, l=l_target, w0=1.0, z=z_norm * math.pi), dx)
            weights = modal_weights(field, basis, dx)
            by_l, by_p = summarize_weights(weights)
            rows.append(
                {
                    "case": "axisymmetric_z_offset",
                    "l_target": l_target,
                    "control": z_norm,
                    "target_l_weight": by_l.get(l_target, 0.0),
                    "other_l_weight": sum(v for k, v in by_l.items() if k != l_target),
                    "p0_weight": by_p.get(0, 0.0),
                    "p1_weight": by_p.get(1, 0.0),
                    "p2plus_weight": sum(v for k, v in by_p.items() if k >= 2),
                    "target_mode_weight": weights.get((0, l_target), 0.0),
                }
            )

        for shift in shift_values:
            field = normalize_field(lg_mode_cartesian(x, y, p=0, l=l_target, w0=1.0, shift_x=shift), dx)
            weights = modal_weights(field, basis, dx)
            by_l, by_p = summarize_weights(weights)
            rows.append(
                {
                    "case": "lateral_shift",
                    "l_target": l_target,
                    "control": shift,
                    "target_l_weight": by_l.get(l_target, 0.0),
                    "other_l_weight": sum(v for k, v in by_l.items() if k != l_target),
                    "p0_weight": by_p.get(0, 0.0),
                    "p1_weight": by_p.get(1, 0.0),
                    "p2plus_weight": sum(v for k, v in by_p.items() if k >= 2),
                    "target_mode_weight": weights.get((0, l_target), 0.0),
                }
            )

        for tilt in tilt_values:
            field = normalize_field(base * np.exp(1j * tilt * x), dx)
            weights = modal_weights(field, basis, dx)
            by_l, by_p = summarize_weights(weights)
            rows.append(
                {
                    "case": "phase_tilt_x",
                    "l_target": l_target,
                    "control": tilt,
                    "target_l_weight": by_l.get(l_target, 0.0),
                    "other_l_weight": sum(v for k, v in by_l.items() if k != l_target),
                    "p0_weight": by_p.get(0, 0.0),
                    "p1_weight": by_p.get(1, 0.0),
                    "p2plus_weight": sum(v for k, v in by_p.items() if k >= 2),
                    "target_mode_weight": weights.get((0, l_target), 0.0),
                }
            )
    return rows


def build_figure(path: Path, radial_rows: list[dict], lmix_rows: list[dict], l_values: list[int], eta_values: list[float]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    ax1, ax2, ax3, ax4 = axes.flat

    for l in l_values:
        rows = [row for row in radial_rows if row["family"] == "axisymmetric_size_mismatch" and row["l"] == l and row["eta"] == eta_values[0] and isinstance(row["p"], int)]
        ax1.plot([row["p"] for row in rows], [row["power"] for row in rows], marker="o", label=fr"$l={l}, \eta={eta_values[0]:.2f}$")
    ax1.set_title("Higher p drops rapidly for mild waist mismatch")
    ax1.set_xlabel(r"$p$")
    ax1.set_ylabel(r"$|c_{p,l}|^2$")
    ax1.set_yscale("log")
    ax1.grid(alpha=0.3)
    ax1.legend()

    for l in l_values:
        y = []
        for eta in eta_values:
            p1 = radial_mismatch_power(l, 1, eta)
            p2 = radial_mismatch_power(l, 2, eta)
            y.append(p2 / p1 if p1 > 0 else 0.0)
        ax2.plot(eta_values, y, marker="o", label=fr"$l={l}$")
    ax2.set_title(r"Suppression factor $|c_{2,l}|^2/|c_{1,l}|^2$")
    ax2.set_xlabel(r"$\eta$")
    ax2.set_ylabel("ratio")
    ax2.grid(alpha=0.3)
    ax2.legend()

    for case, marker in [("axisymmetric_z_offset", "o"), ("lateral_shift", "s"), ("phase_tilt_x", "^")]:
        rows = [row for row in lmix_rows if row["case"] == case and row["l_target"] == l_values[-1]]
        ax3.plot([row["control"] for row in rows], [row["other_l_weight"] for row in rows], marker=marker, label=case)
    ax3.set_title(fr"$l$-mixing weight for target $l={l_values[-1]}$")
    ax3.set_xlabel("control parameter")
    ax3.set_ylabel("power outside target l")
    ax3.grid(alpha=0.3)
    ax3.legend()

    for case, marker in [("axisymmetric_z_offset", "o"), ("lateral_shift", "s"), ("phase_tilt_x", "^")]:
        rows = [row for row in lmix_rows if row["case"] == case and row["l_target"] == l_values[-1]]
        ax4.plot([row["control"] for row in rows], [row["target_mode_weight"] for row in rows], marker=marker, label=case)
    ax4.set_title(fr"Target-mode weight for target $l={l_values[-1]}$")
    ax4.set_xlabel("control parameter")
    ax4.set_ylabel(r"$|c_{0,l}|^2$")
    ax4.grid(alpha=0.3)
    ax4.legend()

    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def build_summary(path: Path, radial_rows: list[dict], lmix_rows: list[dict], l_values: list[int], eta_values: list[float], p_max: int) -> None:
    lines = [
        "Radial-order and l-mixing proof summary",
        "",
        "1) Exact radial-order law for axisymmetric waist mismatch",
        "   For input LG_0^l with eta = w_in / w_0 and preserved cylindrical symmetry, the exact same-l radial decomposition obeys",
        "   |c_{p,l}|^2 = C(p+|l|, p) * [2 eta / (1+eta^2)]^(2|l|+2) * [(1-eta^2)/(1+eta^2)]^(2p).",
        "   Therefore the small parameter is s = (1-eta^2)/(1+eta^2), and each extra radial order brings another factor s^2.",
        "   Adjacent-order ratio:",
        "   |c_{p+1,l}|^2 / |c_{p,l}|^2 = ((p+|l|+1)/(p+1)) * s^2.",
        "",
        "2) Why p=1 is the first thing to worry about",
        "   When eta = 1 + eps with |eps| << 1, one has s ~= -eps, so",
        "   p=1 scales as O(eps^2), p=2 scales as O(eps^4), p=3 scales as O(eps^6).",
        "   Hence p=1 is the leading observable parasitic radial term under mild mismatch.",
        "",
        "Representative exact powers:",
    ]

    for l in l_values:
        for eta in eta_values:
            parts = [f"  l={l}, eta={eta:.2f}:"]
            for p in range(min(p_max, 4) + 1):
                parts.append(f"p={p} -> {100*radial_mismatch_power(l,p,eta):.4f}%")
            lines.append(" ".join(parts))

    lines.extend(
        [
            "",
            "3) Why l stays fixed for axisymmetric mismatch",
            "   If E_in(r,phi) = f(r) exp(i l_target phi), then projection onto cavity LG_p^{l'} gives",
            "   c_{p,l'} propto integral dphi exp(i(l_target-l')phi) = 2 pi delta_{l',l_target}.",
            "   So waist-size mismatch, waist-position mismatch, curvature mismatch, and centered circular clipping can change p, but cannot change l as long as cylindrical symmetry about the same axis is preserved.",
            "",
            "4) When l-mixing appears",
            "   l-mixing requires symmetry breaking: lateral decentering, angular tilt, astigmatism, or off-center clipping.",
            "   For tilt along x, exp(i k_x x) = exp(i k_x r cos phi) = sum_m i^m J_m(k_x r) exp(i m phi),",
            "   so multiplying LG_0^l immediately generates l+m components.",
            "",
            "Representative numerical decomposition (power summed over retained basis window):",
        ]
    )

    for row in lmix_rows:
        lines.append(
            f"  case={row['case']}, l_target={row['l_target']}, control={float(row['control']):.3f}: "
            f"target_l={100*float(row['target_l_weight']):.3f}%, other_l={100*float(row['other_l_weight']):.3f}%, "
            f"target_mode={100*float(row['target_mode_weight']):.3f}%, p1={100*float(row['p1_weight']):.3f}%, "
            f"p>=2={100*float(row['p2plus_weight']):.3f}%"
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(__file__).resolve().parent
    l_values = parse_int_list(args.l_list)
    eta_values = parse_float_list(args.eta_list)
    shift_values = parse_float_list(args.shift_list)
    tilt_values = parse_float_list(args.tilt_list)
    zoff_values = parse_float_list(args.zoff_list)

    radial_rows = build_radial_rows(l_values, eta_values, args.p_max)
    lmix_rows = build_lmix_rows(
        l_values=l_values,
        p_max=args.p_max,
        l_span=args.l_span,
        grid_size=args.grid_size,
        extent=args.extent,
        shift_values=shift_values,
        tilt_values=tilt_values,
        zoff_values=zoff_values,
    )

    write_csv(out_dir / f"{args.output_prefix}radial_table.csv", radial_rows)
    write_csv(out_dir / f"{args.output_prefix}lmix_table.csv", lmix_rows)
    build_figure(out_dir / f"{args.output_prefix}curves.png", radial_rows, lmix_rows, l_values, eta_values)
    build_summary(out_dir / f"{args.output_prefix}summary.txt", radial_rows, lmix_rows, l_values, eta_values, args.p_max)


if __name__ == "__main__":
    main()
