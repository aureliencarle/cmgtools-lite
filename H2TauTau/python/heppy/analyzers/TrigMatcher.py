from PhysicsTools.Heppy.analyzers.core.Analyzer import Analyzer
from PhysicsTools.HeppyCore.utils.deltar import deltaR2

class TrigMatcher(Analyzer):
    '''Performs trigger matching on the first di-lepton 
    in the source collection.

    Example::
        leptons = cfg.Analyzer(
          TrigMatcher,
          src = 'dileptons',
          require_all_matched = False,
          )    

    @param src: the input di-lepton collection

    @param require_all_matched: if true, require trigger matching on both legs
    '''

    def beginLoop(self, setup):
        super(TrigMatcher, self).beginLoop(setup)
        self.counters.addCounter('TrigMatcher')
        count = self.counters.counter('TrigMatcher')
        count.register('all events')
        count.register('trig matched')
    

    def process(self, event):
        '''event must contain
        
        * self.cfg_ana.src: collection of di-leptons to be matched
        '''
        count = self.counters.counter('TrigMatcher')
        count.inc('all events')
        srcs = [getattr(event, src) for src in self.cfg_ana.srcs]
        if len(self.cfg_comp.triggers) > 0:
            matched_glob = 0
            for src in srcs:
                for ptc in src:
                    matched = self.trigMatched(event, ptc)
                    if matched: 
                        matched_glob += 1
            if matched_glob>0: 
                count.inc('trig matched')


    def trigMatched(self, event, ptc, ptMin=None, etaMax=None):
        '''Check that at least one trigger object is matched to the corresponding
        leg. If require_all_matched is True, 
        requires that each single trigger object has a match.'''
        matched = False
        ptc.matchedPaths = set()
        # if hasattr(self.cfg_ana, 'filtersToMatch'):
        #     filtersToMatch = self.cfg_ana.filtersToMatch[0]
        #     legs = [diL.leg1(), diL.leg2()]
        #     leg = legs[self.cfg_ana.filtersToMatch[1] - 1]
        #     triggerObjects = self.handles['triggerObjects'].product()
        #     for item in product(triggerObjects, filtersToMatch):
        #         to     = item[0]
        #         filter = item[1]
        #         print to.filterLabels()[-1], to.filterLabels()[-1] != filter
        #         if to.filterLabels()[-1] != filter:
        #             continue
        #         if self.trigObjMatched(to, leg):
        #             setattr(leg, filter, to)
                    
        if not self.cfg_comp.triggerobjects:
            if self.cfg_ana.verbose:
                print 'No trigger objects configured; auto-passing trigger matching'
            return True

        for info in event.trigger_infos:
            if not info.fired:
                continue
            for to, to_names in zip(info.leg1_objs + info.leg2_objs, info.leg1_names + info.leg2_names):
                if ptMin and to.pt() < ptMin:
                    continue
                if etaMax and abs(to.eta()) > etaMax:
                    continue
                if self.trigObjMatched(to, ptc, to_names):
                    ptc.matchedPaths.add(info.name)
                    matched = True
        return matched


    def trigObjMatched(self, to, leg, names=None, dR2Max=0.25):  # dR2Max=0.089999
        '''Returns true if the trigger object is matched to one of the given
        legs'''
        eta = to.eta()
        phi = to.phi()
        to.matched = False
        if deltaR2(eta, phi, leg.eta(), leg.phi()) < dR2Max:
            to.matched = True
            if hasattr(leg, 'triggerobjects'):
                if to not in leg.triggerobjects:
                    leg.triggerobjects.append(to)
            else:
                leg.triggerobjects = [to]
            if names:
                if hasattr(leg, 'triggernames'):
                    leg.triggernames.update(names)
                else:
                    leg.triggernames = set(names)
        return to.matched
