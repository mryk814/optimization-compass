"""Exact subset oracles, LP/MILP cross-checks, and capacity diagrams."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/discrete-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/discrete-cache')
from pathlib import Path
from itertools import product
from fractions import Fraction as F
import json,platform,numpy as np,scipy
from scipy.optimize import Bounds,LinearConstraint,milp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
P=Path(__file__).resolve().parent
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':font.get_name(),'font.size':11,'svg.fonttype':'path'})
names='ABCD';w=[4,3,5,2];v=[8,5,6,4];W=8
rows=[{'bits':list(x),'name':''.join(n for n,z in zip(names,x) if z) or 'none','weight':sum(a*b for a,b in zip(w,x)),'value':sum(a*b for a,b in zip(v,x))} for x in product([0,1],repeat=4)]
feasible=[r for r in rows if r['weight']<=W];best=max(feasible,key=lambda r:r['value']);assert best['name']=='AB' and best['value']==13
# Value/weight ties are broken by input order; D then A leads to the same subset.
order=sorted(range(4),key=lambda i:-F(v[i],w[i]));remain=W;greedy=[]
for i in order:
 if w[i]<=remain:greedy.append(i);remain-=w[i]
assert [names[i] for i in greedy]==['A','D']
x=[F(1),F(2,3),F(0),F(1)];upper=sum(a*b for a,b in zip(v,x));assert upper==F(46,3)
checks=[]
for integer in [False,True]:
 r=milp(c=-np.array(v),constraints=LinearConstraint([w],ub=W),integrality=np.ones(4) if integer else np.zeros(4),bounds=Bounds(0,1))
 assert r.success;assert abs(-r.fun-(13 if integer else float(upper)))<1e-9
 checks.append({'integer':integer,'status':r.status,'x':r.x.tolist(),'value':-r.fun})
sets={'A':{1,2,3,4},'B':{1,2,5},'C':{3,4,6},'D':{5},'E':{6}};universe=set(range(1,7));coverrows=[]
for y in product([0,1],repeat=5):
 chosen=[n for n,z in zip(sets,y) if z];covered=set().union(*(sets[n] for n in chosen))
 if covered==universe:coverrows.append(chosen)
coverbest=min(coverrows,key=len);assert coverbest==['B','C'] and len(coverbest)==2
uncovered=set(universe);covergreedy=[]
while uncovered:
 n=max(sets,key=lambda n:len(sets[n]&uncovered));gain=sets[n]&uncovered
 assert gain;covergreedy.append(n);uncovered-=gain
assert covergreedy==['A','B','C']
# Retained disaster-mitigation example: a distinct application with its own data.
appw=[4,3,2,3];appv=[9,6,4,5]
app=[(sum(a*z for a,z in zip(appv,bits)),bits) for bits in product([0,1],repeat=4) if sum(a*z for a,z in zip(appw,bits))<=7]
assert max(app)==(15,(1,1,0,0))

cover=np.array([[int(e in sets[n]) for n in sets] for e in range(1,7)])
r=milp(c=np.ones(5),constraints=LinearConstraint(cover,lb=1),integrality=np.ones(5),bounds=Bounds(0,1));assert r.success and r.fun==2
bad=milp(c=np.ones(5),constraints=LinearConstraint(np.vstack([cover,np.zeros(5)]),lb=1),integrality=np.ones(5),bounds=Bounds(0,1));assert bad.status==2
fig,ax=plt.subplots(figsize=(11.4,5.3),layout='constrained');colors={'A':'#387ca4','B':'#d48a34','C':'#8463a2','D':'#359889'}
examples=[('比の貪欲法',[('A',1),('D',1)],'価値 12'),('0–1 の最適解',[('A',1),('B',1)],'価値 13'),('容量を使い切る',[('B',1),('C',1)],'価値 11'),('分数を許す LP',[('A',1),('D',1),('B',F(2,3))],'上界 46/3 ≈ 15.33')]
for y,(label,items,value) in enumerate(examples):
 left=0
 for name,f in items:
  width=w[names.index(name)]*float(f);ax.barh(y,width,left=left,height=.55,color=colors[name],edgecolor='white',hatch='///' if f!=1 else None)
  ax.text(left+width/2,y,name if f==1 else 'B × 2/3',ha='center',va='center',color='white',fontweight='bold',fontsize=12);left+=width
 if left<W:
  ax.barh(y,W-left,left=left,height=.55,color='#ecf0f3',edgecolor='white');ax.text((W+left)/2,y,f'余り {W-left:g}',ha='center',va='center',fontsize=10,color='#536774')
 ax.text(8.2,y,value,va='center',fontsize=12)
ax.axvline(8,color='#6e8796',ls='--');ax.set_xlim(0,11.35);ax.set_xticks(range(9));ax.set_yticks(range(4),[e[0] for e in examples]);ax.invert_yaxis();ax.set_xlabel('重さの合計（容量8）');ax.set_title('同じ4品目：0–1 の答えと分数緩和を分ける',loc='left',fontweight='bold',pad=18)
for sp in ['top','right','left']:ax.spines[sp].set_visible(False)
ax.grid(axis='x',alpha=.14);ax.set_axisbelow(True)
for ext in ['svg','png']:fig.savefig(P/f'knapsack-four-items-bound.{ext}',dpi=180)
report={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'total_subsets':16,'feasible_subsets':len(feasible),'best':best,'greedy_items':[names[i] for i in greedy],'greedy_value':12,'fractional_x':[str(a) for a in x],'fractional_upper_bound':str(upper),'rounded_fractional_weight':9,'solver_checks':checks,'all_subsets':rows,'retained_disaster_example_optimum':{'value':15,'bits':[1,1,0,0]},'set_cover':{'total_subsets':32,'optimum':coverbest,'cost':2,'greedy':covergreedy,'uncoverable_element_solver_status':bad.status}}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'best':best,'feasible':len(feasible),'upper':str(upper),'cover':coverbest},ensure_ascii=False))
