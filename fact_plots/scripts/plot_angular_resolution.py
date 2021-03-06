import click
from fact.io import read_h5py
from ..plotting import add_preliminary
from ..angular_resolution import plot_angular_resolution
import matplotlib.pyplot as plt
from ruamel.yaml import YAML
import numpy as np

yaml = YAML(typ='safe')


plot_config = {
    'xlabel': r'$E_{\mathrm{true}} \,\, / \,\, \mathrm{GeV}$',
    'ylabel': r'$\theta_{0.68} \,\, / \,\, ^\circ$',
    'preliminary_position': 'upper left',
    'preliminary_size': 20,
    'preliminary_color': 'lightgray',
}


@click.command()
@click.argument('gamma_path')
@click.option(
    '--std', default=False, is_flag=True,
    help='Use std instead of inter-percentile distance',
)
@click.option('--threshold', type=float)
@click.option('-c', '--config', help='Path to yaml config file')
@click.option('-o', '--output')
@click.option(
    '--only-correct', is_flag=True,
    help='Show only events with correctly classified sgn(disp)'
)
@click.option('--preliminary', is_flag=True, help='add preliminary')
@click.option('--n-bins', type=int, default=20, help='Number of bins for the area')
@click.option('--e-low', type=float, help='Lower energy limit in GeV')
@click.option('--e-high', type=float, help='Upper energy limit in GeV')
def main(
    gamma_path,
    std,
    n_bins,
    threshold,
    config,
    output,
    only_correct,
    preliminary,
    e_low,
    e_high,
):
    '''
    Plot the 68% containment radius for different energy bins

    ARGUMENTS

    GAMMA_PATH: HDF5 file for simulated gamma rays containing the keys
        * gamma_prediction
        * theta_deg
        * corsika_event_header_total_energy
    '''
    if config:
        with open(config) as f:
            plot_config.update(yaml.load(f))

    columns = [
        'corsika_event_header_total_energy',
        'theta_deg'
    ]

    if threshold is not None:
        columns += ['gamma_prediction']

    if only_correct:
        columns += ['true_disp', 'disp_prediction']

    df = read_h5py(
        gamma_path,
        columns=columns,
        key='events',
    )

    if threshold:
        df = df.query('gamma_prediction >= @threshold').copy()

    if only_correct:
        correct = np.sign(df['disp_prediction']) == np.sign(df['true_disp'])
        df = df.loc[correct].copy()

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.grid()

    if preliminary:
        add_preliminary(
            plot_config['preliminary_position'],
            size=plot_config['preliminary_size'],
            color=plot_config['preliminary_color'],
            ax=ax,
        )

    e_low = e_low or df['corsika_event_header_total_energy'].min()
    e_high = e_high or df['corsika_event_header_total_energy'].max()
    bins = np.logspace(np.log10(e_low), np.log10(e_high), n_bins + 1)

    plot_angular_resolution(df, bins=bins, ax=ax)

    ax.set_xlabel(plot_config['xlabel'])
    ax.set_ylabel(plot_config['ylabel'])

    fig.tight_layout(pad=0)

    if output:
        fig.savefig(output, dpi=300)
    else:
        plt.show()


if __name__ == '__main__':
    main()
