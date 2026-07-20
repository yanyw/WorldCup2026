import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
from wc_model.score import core_markets,dc_matrix,de_vig
from wc_model.ensemble import sharp_consensus
from wc_model.valuation import confidence_class,contract_probability

class TestModel(unittest.TestCase):
    def setUp(self): self.m=dc_matrix(1.2,1.75,-0.08,10);self.a={"away_share_if_90m_draw":.6,"penalties_given_90m_draw":.55,"first_half_goal_share":.4}
    def test_matrix(self): self.assertAlmostEqual(float(self.m.sum()),1,places=10)
    def test_1x2(self):
        x=core_markets(self.m);self.assertAlmostEqual(x["home"]+x["draw"]+x["away"],1,places=10)
    def test_devig(self): self.assertAlmostEqual(sum(de_vig({"a":2,"b":2.1}).values()),1,places=10)
    def test_sharp_consensus_is_normalized(self):
        books=[{"decimal_1x2":{"home":2.2,"draw":3.2,"away":3.4},"decimal_total_2_5":{"over":2.0,"under":1.9}},
               {"decimal_1x2":{"home":2.3,"draw":3.1,"away":3.3},"decimal_total_2_5":{"over":2.1,"under":1.8}}]
        one,total=sharp_consensus(books)
        self.assertAlmostEqual(sum(one.values()),1,places=10)
        self.assertAlmostEqual(sum(total.values()),1,places=10)
    def test_exact_scores_partition(self):
        s=sum(contract_probability("exact_score",f"Norway {h}-{a} England",self.m,"Norway","England",self.a) for h in range(4) for a in range(4))
        other=contract_probability("exact_score","Any other score",self.m,"Norway","England",self.a);self.assertAlmostEqual(s+other,1,places=10)
    def test_full_match_btts_uses_matrix(self):
        actual=contract_probability("btts","Both teams to score",self.m,"Norway","England",self.a)
        self.assertAlmostEqual(actual,float(self.m[1:,1:].sum()),places=10)
    def test_half_btts_is_low_confidence(self):
        self.assertEqual(confidence_class("btts","Both teams to score first half"),"low")
        self.assertEqual(confidence_class("btts","Both teams to score"),"standard")
    def test_total_partition(self):
        over=contract_probability("totals","Total over 2.5",self.m,"Norway","England",self.a)
        self.assertAlmostEqual(over+float(sum(self.m[i,j] for i in range(3) for j in range(3-i))),1,places=10)

if __name__=="__main__":unittest.main()
