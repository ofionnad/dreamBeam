"""Script to generate LOFAR antenna response data."""
import numpy
import re
import pickle
from antpat.dualpolelem import DualPolElem
from antpat.reps.hamaker import HamakerPolarimeter
from dreambeam.telescopes import rt
from dreambeam.telescopes.geometry_ingest import readarrcfg, readalignment
from dreambeam.telescopes.LOFAR.feeds import LOFAR_LBA_stn, LOFAR_HBA_stn, LOFAR_LHBA_stn

TELESCOPE_NAME = 'LOFAR'
NR_POLS = 2
SAMPFREQ = 100e6
NR_CHANNELS = 512
BANDS = ['LBA', 'HBA']
ANTMODELS = ['Hamaker']
OOSR2 = 1./numpy.sqrt(2)
PICKLE_PROTO = pickle.HIGHEST_PROTOCOL
# Rotation of LOFAR antennas from build frame to station frame.
# It takes x/y and directed dipoles and places them along (-1,-1)/(+1,-1) resp.
POLCRDROT = numpy.array([[-OOSR2, +OOSR2,  0.],
                         [-OOSR2, -OOSR2,  0.],
                         [    0.,     0.,  1.]])
LOFAR_HA_DATADIR = './share/'  # Dir for native telescope project data.
TELEDATADIR = 'data/'          # Dir for telescope data for RIME level work.
HA_LBA_FILE_DEF = TELEDATADIR+'HA_LOFAR_elresp_LBA.p'
HA_HBA_FILE_DEF = TELEDATADIR+'HA_LOFAR_elresp_HBA.p'
DP_LBA_FILE_DEF = TELEDATADIR+'DP_model_LBA.p'
DP_HBA_FILE_DEF = TELEDATADIR+'DP_model_HBA.p'
DP_BAFILES = {'LBA': DP_LBA_FILE_DEF, 'HBA': DP_HBA_FILE_DEF}

bands = DP_BAFILES.keys()

#Start up a telescope wizard:
tw = rt.TelescopesWiz()


def read_LOFAR_HAcc(coefsccfilename):
    """Read Hamaker-Arts coefficients from c++ header files used in the
    "lofar_element_response" code developed at ASTRON for LOFAR. It contains
    LOFAR specific constructs such as reference to "lba" and "hba", so it is not
    suitable for other projects.
    """
    re_fcenter = r'[lh]ba_freq_center\s*=\s*(?P<centerstr>.*);'
    re_frange  = r'[lh]ba_freq_range\s*=\s*(?P<rangestr>.*);'
    re_shape   = r'default_[lh]ba_coeff_shape\[3\]\s*=\s*\{(?P<lstshp>[^\}]*)\}'
    re_hl_ba_coeffs_lst = r'(?P<version>\w+)(?P<band>[hl]ba)_coeff\s*\[\s*(?P<nrelem>\d+)\s*\]\s*=\s*\{(?P<cmplstr>[^\}]*)\}'
    re_cc_cmpl_coef = r'std::complex<double>\((.*?)\)'
    with open(coefsccfilename, 'r') as coefsccfile:
        coefsfile_content = coefsccfile.read()
    searchres = re.search(re_fcenter, coefsfile_content)
    freq_center = float(searchres.group('centerstr'))
    searchres = re.search(re_frange, coefsfile_content)
    freq_range = float(searchres.group('rangestr'))
    searchres = re.search(re_shape, coefsfile_content)
    lstshp = [int(lstshpel) for lstshpel in searchres.group('lstshp').split(',')]
    lstshp.append(NR_POLS)
    searchres = re.search(re_hl_ba_coeffs_lst, coefsfile_content, re.M)
    HAcoefversion = searchres.group('version')
    HAcoefband = searchres.group('band')
    HAcoefnrelem = searchres.group('nrelem')
    lstofCmpl = re.findall(re_cc_cmpl_coef, searchres.group('cmplstr'))
    cmplx_lst = []
    for reimstr in lstofCmpl:
        reimstrs = reimstr.split(',')
        cmplx_lst.append( complex(float(reimstrs[0]), float(reimstrs[1])) )
    coefs = numpy.reshape(numpy.array(cmplx_lst), lstshp)
    #The coefficients are order now as follows:
    #coefs[k,theta,freq,spherical-component].shape == (2,5,5,2)
    artsdata={'coefs': coefs, 'HAcoefversion': HAcoefversion,
              'HAcoefband': HAcoefband, 'HAcoefnrelem': HAcoefnrelem,
              'freq_center': freq_center, 'freq_range': freq_range}
    return artsdata


def convLOFARcc2HA(inpfile, outfile, channels):
    """Convert a .cc file of the Hamaker-Arts model to a file with a pickled
    dict of a Hamaker-Arts instance."""
    artsdata = read_LOFAR_HAcc(inpfile)
    artsdata['channels'] = channels
    pickle.dump(artsdata, open(outfile, 'wb'), PICKLE_PROTO)


def convHA2DPE(inp_HA_file, out_DP_file):
    """Convert a file with a pickled dict of a Hamaker-Arts instance to a
    file with a pickled DualPolElem object."""
    artsdata = pickle.load(open(inp_HA_file, 'rb'))
    HLBA = HamakerPolarimeter(artsdata)
    stnDPolel = DualPolElem(HLBA)
    pickle.dump(stnDPolel, open(out_DP_file, 'wb'), PICKLE_PROTO)


def gen_antmodelfiles(inpfileL=LOFAR_HA_DATADIR+'DefaultCoeffLBA.cc',
                       inpfileH=LOFAR_HA_DATADIR+'DefaultCoeffHBA.cc',
                       outfileL=HA_LBA_FILE_DEF,
                       outfileH=HA_HBA_FILE_DEF
                       ):
    """A convenience function to produce the pickled 'artsdata' for the default
    LOFAR model data stored in the 'lofar_elem_resp' packages c++ header files.
    Also adds nominal LOFAR frequency channels."""

    # Adding nominal frequency channels. The HA model for LOFAR has two bands
    # while data recording S/W has 3 intervals based on sampling frequency,
    # namely (0,100), (100,200), (200,300), each with 512 channels.
    # Here I concatenate the two latter intervals.

    channels = numpy.linspace(0., SAMPFREQ, NR_CHANNELS, endpoint=False)
    convLOFARcc2HA(inpfileL, outfileL, channels)
    inpfileL = outfileL
    convHA2DPE(inpfileL, DP_LBA_FILE_DEF)
    channels = numpy.linspace(SAMPFREQ, 3*SAMPFREQ, 2*NR_CHANNELS, endpoint=False)
    convLOFARcc2HA(inpfileH, outfileH, channels)
    inpfileH = outfileH
    convHA2DPE(inpfileH, DP_HBA_FILE_DEF)


def save_telescopeband(band, antmodel='Hamaker'):
    """Save all the data relevant to the telescope-band beam modeling into
    one file."""
    assert band in bands, ("Error: {} is not one of the available bands.\n"
                           "(Available bands are: {})").format(band, bands)
    assert antmodel in ANTMODELS, ("Error: {} is not one of the available models.\n"
                                  "Available models are: {})").format(antmodel, ANTMODELS)
    print("Generating '{}' beam-model for the band {} of the {} telescope with stations:".format(
                                                   antmodel, band, TELESCOPE_NAME))
    # Create telescope-bands metadata:
    telescope = {'Name': TELESCOPE_NAME, 'Band': band, 'Beam-model': antmodel}
    #   * Create station's antenna model
    DP_BAfile = DP_BAFILES[band]
    if antmodel == 'Hamaker':
        #This is an example of dual-pol element built from a monolithic
        #Jones representation.
        stnDPolel = pickle.load(open(DP_BAfile, 'rb'))
    #Rotate 45 degrees since LOFAR elements are 45 degrees to meridian:
    stnDPolel.rotateframe(POLCRDROT)

    #Create telescope_band_station metadata:
    telescope['Station'] = {}
    if band == BANDS[0]:
        LOFAR_BA_stn = LOFAR_LBA_stn
    else:
        LOFAR_BA_stn = LOFAR_HBA_stn
    LOFAR_BA_stn = LOFAR_LHBA_stn
    x, y, z, diam, stnIds = readarrcfg(TELESCOPE_NAME, band)

    for stnId in stnIds:
        print(stnId)
        #    *Setup station Jones*
        # Get metadata for the LOFAR station. stnRot is transformation matrix
        #  ITRF_crds = stnRot*LOFAR_crds
        stnid_idx = stnIds.tolist().index(stnId)
        stnPos = [x[stnid_idx], y[stnid_idx], z[stnid_idx]]
        stnRot = readalignment(TELESCOPE_NAME, stnId, band)
        # Create a StationBand object for this
        stnbnd = LOFAR_BA_stn(stnPos, stnRot)
        stnbnd.feed_pat = stnDPolel
        telescope['Station'][stnId] = stnbnd
    teldatdir, saveName = tw.telbndmdl2dirfile(TELESCOPE_NAME, band, antmodel)
    pickle.dump(telescope, open('/'.join((teldatdir, saveName)), 'wb'), PICKLE_PROTO)
    print("Saved '"+saveName+"' in "+teldatdir)


if __name__ == "__main__":
    """Use this to produce telescope data files for use in dreamBeam, or when
    configuration data has changed. Run this as:
    $ python telwizhelper.py
    """
    gen_antmodelfiles()
    #stnlst = list_stations(TELESCOPE_NAME)
    antmodel = 'Hamaker'
    for band in BANDS:
        #save_telescopeband(band, stnlst, antmodel)
        save_telescopeband(band, antmodel)
    print("Completed setup.")
