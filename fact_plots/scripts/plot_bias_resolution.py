import click
from fact.io import read_h5py
from ..plotting import add_preliminary
from ..bias_resolution import plot_bias_resolution
import matplotlib.pyplot as plt
from ruamel.yaml import YAML
import numpy as np


plot_config = {
    'xlabel_true': r'$E_{\mathrm{true}} \,\, / \,\, \mathrm{GeV}$',
    'xlabel_est': r'$E_{\mathrm{est}} \,\, / \,\, \mathrm{GeV}$',
    'preliminary_position': 'upper right',
    'preliminary_size': 20,
    'preliminary_color': 'lightgray',
}

yaml = YAML(typ='safe')


@click.command()
@click.argument('gamma_path')
@click.option(
    '--std', default=False, is_flag=True,
    help='Use std instead of inter-percentile distance',
)
@click.option('--n-bins', default=20, type=int)
@click.option('--e-low', type=float, help='Lower energy limit in GeV')
@click.option('--e-high', type=float, help='Upper energy limit in GeV')
@click.option('--threshold', type=float)
@click.option('--theta2-cut', type=float)
@click.option('-c', '--config', help='Path to yaml config file')
@click.option('-o', '--output')
@click.option('--preliminary', is_flag=True, help='add preliminary')
@click.option('--estimated', is_flag=True, help='Plot vs. estimated energy')
def main(gamma_path, std, n_bins, e_low, e_high, threshold, theta2_cut, config, output, preliminary, estimated):
    ''' Plot energy bias and resolution for simulated gamma ray events vs true energy

    ARGUMENTS:

        GAMMA_PATH: hdf5 file containing the keys
            * gamma_energy_prediction
            * corsika_event_header_total_energy
            * gamma_prediction
            * theta_deg
    '''
    if config:
        with open(config) as f:
            plot_config.update(yaml.load(f))

    df = read_h5py(
        gamma_path,
        key='events',
        columns=[
            'gamma_energy_prediction',
            'corsika_event_header_total_energy',
            'gamma_prediction',
            'theta_deg'
        ],
    )

    if threshold:
        df = df.query('gamma_prediction >= @threshold').copy()
    if theta2_cut:
        df = df.query('theta_deg**2 <= @theta2_cut').copy()

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

    ax_bias, ax_res = plot_bias_resolution(
        df, bins=bins, std=std, ax_bias=ax,
        estimated=estimated
    )

    if estimated:
        ax_bias.set_xlabel(plot_config['xlabel_est'])
    else:
        ax_bias.set_xlabel(plot_config['xlabel_true'])

    ax_bias.set_ylabel('Bias', color='C0')
    ax_res.set_ylabel('Resolution', color='C1')

    l1, h1 = ax_bias.get_ylim()
    l2, h2 = ax_res.get_ylim()
    l = min(l1, l2)
    h = max(h1, h2)

    ax_res.set_ylim(l, h)
    ax_bias.set_ylim(l, h)

    fig.tight_layout(pad=0.05)

    if output:
        fig.savefig(output, dpi=300)
    else:
        plt.show()


if __name__ == '__main__':
    main()
