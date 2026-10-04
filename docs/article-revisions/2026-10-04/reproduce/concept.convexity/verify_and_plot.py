"""Check the fixed-commit explorable's exact functions and replace its incorrect static sketch."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/oc-foundations-mpl')
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
P=Path(__file__).resolve().parent; (P/'media').mkdir(exist_ok=True)
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font_manager.fontManager.addfont(font)
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':12,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False})
f=lambda x: .35*np.asarray(x)**2+.2
well=lambda x: .18*np.asarray(x)**4-.9*np.asarray(x)**2+.25*np.asarray(x)+1.4
rows=[]
for theta in [0,.25,.5,1]:
 a,b=-2.,2.;z=theta*a+(1-theta)*b;chord=theta*f(a)+(1-theta)*f(b);gap=chord-f(z);exact=.35*theta*(1-theta)*(a-b)**2
 assert np.isclose(gap,exact)
 rows.append({'theta':theta,'mix':z,'f_mix':float(f(z)),'chord':float(chord),'gap':float(gap)})
# Deterministic numerical identity tests supplement, rather than replace, algebra.
rng=np.random.default_rng(0);a=rng.uniform(-2.6,2.6,1000);b=rng.uniform(-2.6,2.6,1000);t=rng.uniform(0,1,1000)
gap=t*f(a)+(1-t)*f(b)-f(t*a+(1-t)*b)
assert np.allclose(gap,.35*t*(1-t)*(a-b)**2,atol=1e-14)
assert np.all(gap>=-1e-14)
assert abs(.3*f(1.2)+.7*f(1.2)-f(1.2)) < 1e-14
assert rows[0]["gap"] == rows[-1]["gap"] == 0
counter=.5*well(-1.5)+.5*well(1.5)-well(0)
assert np.isclose(counter,-1.11375)
roots=np.sort(np.roots([.72,0,-1.8,.25]).real)
stationary=[{'x':float(x),'f':float(well(x)),'second_derivative':float(2.16*x*x-1.8)} for x in roots]
assert well(roots[0]) < well(roots[-1]) and stationary[0]['second_derivative']>0 and stationary[-1]['second_derivative']>0
fig,ax=plt.subplots(figsize=(8,4.6),layout='constrained')
x=np.linspace(-2.3,2.3,500);ax.plot(x,f(x),lw=3,color='#2676a6',label='f(x) = 0.35 x² + 0.2')
ax.plot([-2,2],[1.6,1.6],color='#c76531',lw=2.5,ls='--',label='端点の値を混ぜた弦')
ax.scatter([-2,2],[1.6,1.6],color='#c76531',s=55,zorder=5)
ax.scatter([0,0],[.2,1.6],color=['#2676a6','#c76531'],s=60,zorder=5)
ax.annotate('',(0,1.57),(0,.23),arrowprops={'arrowstyle':'<->','lw':2,'color':'#375247'})
ax.text(.12,.9,'高さの差 1.4',fontsize=12,color='#375247')
ax.annotate('f(0) = 0.2',(0,.2),xytext=(25,-5),textcoords='offset points',color='#2676a6')
ax.text(-2.05,1.7,'a = −2');ax.text(1.52,1.7,'b = 2')
ax.set(xlabel='入力 x',ylabel='関数値',xlim=(-2.45,2.45),ylim=(-.02,2.65),title='二点の中間：入力を混ぜると0、出力を混ぜると1.6')
ax.legend(loc='upper center',frameon=False,ncol=1,fontsize=11);ax.grid(alpha=.14)
for ext in ['svg','png']:fig.savefig(P/'media'/f'convexity.{ext}',dpi=180)
plt.close(fig)
report={'versions':{'numpy':np.__version__,'matplotlib':matplotlib.__version__},'source_commit':'fe6e96666bdef94ae33bdc13a49461e7d2a38962','quadratic':'0.35*x*x + 0.2','chord_rows':rows,'double_well':{'formula':'0.18*x**4 - 0.9*x*x + 0.25*x + 1.4','a':-1.5,'b':1.5,'theta':.5,'at_mix':float(well(0)),'chord':float(.5*well(-1.5)+.5*well(1.5)),'gap':float(counter),'stationary_points':stationary},'nonconvex_domain':{'intervals':[[-2,-1],[2,3]],'local_point':2,'local_value':float(f(2)),'global_point':-1,'global_value':float(f(-1)),'midpoint':.5,'midpoint_feasible':False},'checks':{'quadratic_identity_random_trials':1000,'boundary_theta_zero_one':True,'same_endpoints_gap_zero':True},'tests':'all assertions passed','proof_limit':'Numerical sampling is not proof of convexity; the algebraic identity is given in the article.'}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
