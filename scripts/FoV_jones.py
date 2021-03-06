#!/usr/bin/env python
"""Show LOFAR element beam pattern.
"""
import sys
from datetime import datetime
import numpy as np
from dreambeam.rime.scenarios import primarybeampat
from dreambeam.telescopes.rt import get_tel_plugins
from dreambeam.rime.jones import plotJonesField


def printJonesField(jnf, jbasis):
    (nr_xs, nr_ys, _, _) = jbasis.shape
    print("x, y, J00, J01, J10, J11")
    for idxi in range(nr_xs):
        for idxj in range(nr_ys):
            x = np.real(jbasis[idxi, idxj, 0, 0])
            y = np.real(jbasis[idxi, idxj, 1, 0])
            J00 = jnf[idxi, idxj, 0, 0]
            J01 = jnf[idxi, idxj, 0, 1]
            J10 = jnf[idxi, idxj, 1, 0]
            J11 = jnf[idxi, idxj, 1, 1]
            jones_1f_outstring = ",".join(map(str, [x, y, J00, J01, J10, J11]))
            print(jones_1f_outstring)


def getnextcmdarg(args, mes):
    try:
        arg = args.pop(0)
    except IndexError:
        raise RuntimeError("Specify "+mes)
    return arg


SCRIPTNAME = sys.argv[0].split('/')[-1]
USAGE = """Usage:{}
         print|plot telescope band stnID beammodel timeUTC
         pointingRA pointingDEC frequency""".format(SCRIPTNAME)


def main():
    """
    Plot or print the Jones matrices over the field-of-view.

    Example
    -------
    >>> FoV_jones plot LOFAR LBA SE607 Hamaker 2012-04-01T01:02:03 \
            '6.11,1.02,J2000' 60E6
    """
    # Get telescope plugins
    tp = get_tel_plugins()
    # Process cmd line arguments
    args = sys.argv[1:]
    try:
        action = getnextcmdarg(args, "output-type:\n  'print' or 'plot'")
        telescopename = getnextcmdarg(args, "telescope:\n  "
                                      + ', '.join(tp.keys()))
        band = getnextcmdarg(args, "band/feed:\n  "
                             + ', '.join(tp[telescopename].get_bands()))
        stnid = getnextcmdarg(args, "station-ID:\n  "
                              + ', '.join(tp[telescopename].get_stations(band)))
        antmodel = getnextcmdarg(args, "beam-model:\n  "
                                 + ', '.join(tp[telescopename].get_beammodels(
                                                                         band)))
        try:
            obstime = datetime.strptime(args[0], "%Y-%m-%dT%H:%M:%S")
        except IndexError:
            raise RuntimeError(
                "Specify time (UTC in ISO format: yy-mm-ddTHH:MM:SS ).")
        try:
            (az, el, refframe) = args[1].split(',')
            az, el = float(az), float(el)
        except ValueError:
            raise RuntimeError("Specify pointing direction (in radians):"
                               " 'RA,DEC,J2000' or 'AZ,EL,AZEL'")
        try:
            freq = float(args[2])
        except ValueError:
            raise RuntimeError("Specify frequency (in Hz).")
    except Exception as e:
        raise SystemExit(e)

    if refframe == 'AZEL':
        refframe = 'STN'
        l = np.linspace(-1., 1., 30)
        m = np.linspace(-1., 1., 30)
        ll, mm = np.meshgrid(l, m)
        lmgrid = (ll, mm)
    else:
        lmgrid = None
    pointing = (az, el, refframe)

    # Compute the Jones matrices
    jonesfld, stnbasis, j2000basis = primarybeampat(
                                    telescopename, stnid, band, antmodel, freq,
                                    pointing=pointing, obstime=obstime,
                                    lmgrid=lmgrid)
    if refframe == 'STN':
        jbasis = stnbasis
    else:
        jbasis = j2000basis
    # Do something with resulting Jones according to cmdline args
    if action == "plot":
        plotJonesField(jonesfld, jbasis, refframe, rep='Stokes',
                       mask_belowhorizon=False)
    else:
        printJonesField(jonesfld, jbasis)


if __name__ == "__main__":
    main()
