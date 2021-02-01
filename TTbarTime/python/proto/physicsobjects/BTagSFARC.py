import os
import ROOT
import numpy as np

from ROOT import TRandom3, TFile
ROOT.gSystem.Load('libCondToolsBTau')

#todo: move this to separate BTagSF analyzer that could be configured? 
class BTagSFARC(object):
    '''Translate heppy run 1 BTagSF class to python, and update to 2012.
    '''
    def __init__ (self, seed, wp='loose', year= '2017',tagger = 'DeepCSV', measurement='central') :
        self.randm = TRandom3(seed)

        if year == '2016' :
            if tagger == 'DeepCSV':
                rootfname = '/'.join([os.environ["CMSSW_BASE"],
                                      'src/CMGTools/TTbarTime/data/2016/btag/btag_efficiency_DeepCSV.root'])
                calib = ROOT.BTagCalibration("CSVv2", os.path.expandvars("$CMSSW_BASE/src/CMGTools/TTbarTime/data/2016/btag/DeepCSV_2016LegacySF_V1.csv"))
            if tagger == 'DeepJet':
                rootfname = '/'.join([os.environ["CMSSW_BASE"],
                              'src/CMGTools/TTbarTime/data/2016/btag/btag_efficiency_CSVv2.root'])
                calib = ROOT.BTagCalibration("CSVv2", os.path.expandvars("$CMSSW_BASE/src/CMGTools/TTbarTime/data/2016/btag/DeepJet_2016LegacySF_V1.csv"))
            if tagger == 'CSVv2':
                rootfname = '/'.join([os.environ["CMSSW_BASE"],
                              'src/CMGTools/TTbarTime/data/2016/btag/btag_efficiency_CSVv2.root'])
                calib = ROOT.BTagCalibration("CSVv2", os.path.expandvars("$CMSSW_BASE/src/CMGTools/TTbarTime/data/CSVv2_94XSF_V2_B_F.csv"))

            #tagging_efficiencies_march2018_btageff-all_samp-inc-DeepCSV_medium.root

        self.mc_eff_file = TFile(rootfname)

        # MC b-tag efficiencies as measured in HTT by Adinda
        self.btag_eff_b = self.mc_eff_file.Get('btag_b')
        self.btag_eff_c = self.mc_eff_file.Get('btag_c')
        self.btag_eff_oth = self.mc_eff_file.Get('btag_oth')

        op_dict = {
            'loose':0,
            'medium':1,
            'tight':2
        }
        print 'Booking b/c reader'

        v_sys = getattr(ROOT, 'vector<string>')()
        v_sys.push_back('up')
        v_sys.push_back('down')

        self.reader_bc = ROOT.BTagCalibrationReader(op_dict[wp], measurement, v_sys)
        self.reader_bc.load(calib, 0, 'comb')
        self.reader_bc.load(calib, 1, 'comb')
        print 'Booking light reader'
        self.reader_light = ROOT.BTagCalibrationReader(op_dict[wp], measurement, v_sys)
        self.reader_light.load(calib, 2, 'incl')

    @staticmethod
    def getBTVJetFlav(flav):
        if abs(flav) == 5:
            return 0
        elif abs(flav) == 4:
            return 1
        return 2

    def getMCBTagEff(self, pt, eta, flavor):
        hist = self.btag_eff_oth
        if flavor == 5:
            hist = self.btag_eff_b
        elif flavor == 4:
            hist = self.btag_eff_c

        binx = hist.GetXaxis().FindFixBin(pt)
        biny = hist.GetYaxis().FindFixBin(abs(eta))
        eff = hist.GetBinContent(binx, biny)
        return eff

    def getPOGSFB(self, pt, eta, flavor):
        if flavor in [4, 5]:
            return self.reader_bc.eval_auto_bounds('central', self.getBTVJetFlav(flavor), eta, pt)

        return self.reader_light.eval_auto_bounds('central', self.getBTVJetFlav(flavor), eta, pt)

    def isBTagged(self, jet, pt, eta, csv, jetflavor, is_data, csv_cut=0.5803 ): #CSVv2 loose default
        jetflavor = abs(jetflavor)
        setattr(jet, 'btagWeight', 1.)
        
        SFb = self.getPOGSFB(pt, abs(eta), jetflavor)
        eff_b = self.getMCBTagEff(pt, abs(eta), jetflavor)
        
        if csv > csv_cut:
            if(eff_b != 0):
                jet.btagWeight = (SFb*eff_b)/eff_b
            else:
                jet.btagWeight = 1
            return True
        else:
            if(eff_b != 1):
                jet.btagWeight = (1 - SFb*eff_b)/(1 - eff_b)
            else:
                jet.btagWeight = 1
            return False
    


if __name__ == '__main__':

    btag = BTagSF(12345)
    print 'created BTagSF instance'
    print btag.isBTagged(25., 2.3, 0.9, 5, False)
    print btag.isBTagged(104.3933, -0.885529, 0.9720, 5, False)

