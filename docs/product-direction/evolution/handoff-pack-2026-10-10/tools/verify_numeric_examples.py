#!/usr/bin/env python3
"""Independently verify educational toy examples. Not a test of repo code."""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import json
import math
from pathlib import Path

def verify() -> dict:
    vertices=[(F(0),F(0)),(F(6),F(0)),(F(4),F(3)),(F(0),F(13,3))]
    assert all(3*x+2*y<=18 and x+3*y<=13 and min(x,y)>=0 for x,y in vertices)
    values=[3*x+4*y for x,y in vertices]
    assert max(values)==24 and vertices[values.index(max(values))]==(4,3)
    u,v=F(5,7),F(6,7)
    assert 3*u+v==3 and 2*u+3*v==4 and 18*u+13*v==24
    for b in [F(26,3),F(10),F(18),F(20),F(39)]:
        x,y=(3*b-26)/7,(39-b)/7
        assert x>=0 and y>=0 and 3*x+2*y==b and x+3*y==13
        assert 3*x+4*y==u*b+v*13
    gd=[]
    for alpha in [F(3,50),F(2,25),F(3,25)]:
        x,y=F(2),F(1); fs=[]
        for _ in range(7):
            fs.append(float((x*x+25*y*y)/2)); x,y=(1-alpha)*x,(1-25*alpha)*y
        if alpha==F(3,50): assert all(a>b for a,b in zip(fs,fs[1:]))
        if alpha==F(3,25): assert fs[-1]>fs[0]
        if alpha==F(2,25): assert abs(1-25*alpha)==1
        gd.append({'alpha':float(alpha),'values':fs,'stiff_direction_multiplier':float(1-25*alpha)})
    points=[(F(0),F(2)),(F(1),F(6,5)),(F(2),F(0))]
    for point in points:
        assert not any(all(a<=b for a,b in zip(other,point)) and any(a<b for a,b in zip(other,point)) for other in points)
    assert min((p for p in points if p[1]<=F(6,5)),key=lambda p:p[0])==points[1]
    assert 6/F(11)>4/F(9) # B can never simultaneously beat A and C.
    ot=[]
    for eps in [0.1,1.0,10.0]:
        q=math.exp(-1/eps); diagonal=.5/(1+q); off=.5*q/(1+q)
        assert math.isclose(diagonal+off,.5,abs_tol=1e-12)
        # Stationarity of the strictly convex entropic objective on the transport polytope.
        assert math.isclose(eps*math.log(diagonal),1+eps*math.log(off),abs_tol=1e-10)
        ot.append({'epsilon':eps,'plan':[[diagonal,off],[off,diagonal]],'unregularized_transport_cost':2*off})
    assert ot[0]['unregularized_transport_cost']<ot[1]['unregularized_transport_cost']<ot[2]['unregularized_transport_cost']
    saddle_before=1**2-2**2; saddle_after=0
    assert saddle_after>saddle_before
    return {'status':'passed','scope':'Independent stdlib toy checks, not repository implementation or browser tests',
            'bakery_lp':{'vertices':[[str(a),str(b)] for a,b in vertices], 'objective_values':[str(x) for x in values],
                         'optimum':['4','3'],'value':'24','dual':['5/7','6/7'],'flour_basis_interval':['26/3','39']},
            'gradient_descent':gd,
            'unsupported_pareto_point':{'points':[[0,2],[1,1.2],[2,0]],'B_beats_C_requires_w_at_least':'6/11','B_beats_A_requires_w_at_most':'4/9','simultaneously_possible':False},
            'entropic_transport':ot,
            'newton_saddle':{'function':'x^2-y^2','start':[1,2],'one_step':[0,0],'f_before':saddle_before,'f_after':saddle_after,'stationary_but_not_minimum':True}}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--out',type=Path)
    a=p.parse_args(); result=verify(); text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(text,encoding='utf-8')
    print(text)
if __name__=='__main__': main()
