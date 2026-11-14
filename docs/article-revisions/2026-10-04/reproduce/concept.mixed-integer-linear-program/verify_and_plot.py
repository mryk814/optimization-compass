"""Enumerate the integer model and reproduce one specified five-LP teaching tree."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/oc-foundations-mpl')
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import linprog, milp, Bounds, LinearConstraint
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager
P=Path(__file__).resolve().parent;(P/'media').mkdir(exist_ok=True)
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False})
A=np.array([[6.,4.],[1.,2.]]);b=np.array([24.,6.]);c=np.array([5.,4.])
integer=milp(-c,integrality=np.ones(2),bounds=Bounds(0,np.inf),constraints=LinearConstraint(A,-np.inf,b),options={'mip_rel_gap':0.})
assert integer.success and integer.status==0 and np.allclose(integer.x,[4,0]) and np.isclose(integer.fun,-20)
points=np.array([(i,j) for i in range(5) for j in range(4) if np.all(A@[i,j]<=b)])
assert len(points)==13 and np.array_equal(points[np.argmax(points@c)],[4,0])
raw_nodes=[('root',[(0,None),(0,None)]),('left',[(0,None),(0,1)]),('left_left',[(0,3),(0,1)]),('left_right',[(4,None),(0,1)]),('right',[(0,None),(2,None)])]
nodes=[]
expected={'root':([3,1.5],21),'left':([10/3,1],62/3),'left_left':([3,1],19),'left_right':([4,0],20),'right':([2,2],18)}
for name,bounds in raw_nodes:
 r=linprog(-c,A_ub=A,b_ub=b,bounds=bounds,method='highs');assert r.success
 ex,ev=expected[name];assert np.allclose(r.x,ex) and np.isclose(-r.fun,ev)
 nodes.append({'name':name,'bounds':bounds,'x':r.x.tolist(),'upper_bound':float(-r.fun),'slack':(b-A@r.x).tolist()})
assert np.array_equal(A@[3,2]-b,[2,1])
# Every integer point belongs to a child at each split; none is lost.
assert all(z[1]<=1 or z[1]>=2 for z in points)
assert all(z[0]<=3 or z[0]>=4 for z in points if z[1]<=1)
assert max(n['upper_bound'] for n in nodes if n['name'] in ['left_left','left_right','right']) == 20
# Illustration of a loose valid M: minimize 10*y with x>=4, x<=M*y.
# M=4 gives relaxation y=1, M=100 gives .04, although the integer solution is y=1.
bigm=[]
for M in [4.,100.]:
 rr=linprog([0.,10.],A_ub=[[-1.,0.],[1.,-M]],b_ub=[-4.,0.],bounds=[(0,4),(0,1)],method='highs')
 assert rr.success and np.isclose(rr.fun,40/M)
 bigm.append({'M':M,'relaxed_x_y':rr.x.tolist(),'relaxed_cost':rr.fun,'integer_cost':10.})
fig,axs=plt.subplots(1,2,figsize=(12.5,5.7),layout='constrained',gridspec_kw={'width_ratios':[1,1.15]})
ax=axs[0];poly=np.array([[0,0],[4,0],[3,1.5],[0,3]])
ax.fill(*poly.T,color='#e3eef6');ax.plot(*np.vstack([poly,poly[0]]).T,color='#407598',lw=1.5)
ax.scatter(*points.T,s=40,color='#3e789b',zorder=3)
xx=np.linspace(0,4.4,200)
for v,style,color in [(21,'--','#9d7d44'),(20,'-','#c55c2e')]:
 yy=(v-5*xx)/4;mask=(yy>=0)&(yy<=3.4);ax.plot(xx[mask],yy[mask],ls=style,color=color,lw=1.7)
ax.scatter(3,1.5,s=110,marker='D',color='#aa8b44',zorder=5)
ax.scatter(4,0,s=200,marker='*',color='#c55c2e',zorder=5)
ax.scatter(3,2,s=95,marker='x',color='#b83948',zorder=5)
ax.annotate('LP緩和 (3, 1.5)\n上界 21',(3,1.5),xytext=(1.05,.25),textcoords='data',fontsize=10,arrowprops={'arrowstyle':'-','color':'#9d7d44'},bbox={'facecolor':'white','edgecolor':'none','alpha':.75})
ax.annotate('整数解 (4, 0)\n利益 20',(4,0),xytext=(-92,24),textcoords='offset points',fontsize=10,color='#9d421e')
ax.annotate('丸め (3, 2)\n制約を2本とも破る',(3,2),xytext=(-30,34),textcoords='offset points',fontsize=10)
ax.set(xlim=(-.25,4.45),ylim=(-.35,3.4),xlabel='x1',ylabel='x2',aspect='equal',title='整数解と、LP緩和の上界を分ける');ax.grid(alpha=.12)
ax=axs[1];ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off');ax.set_title('手で指定した分枝：各箱が1個のLP緩和')
positions={'root':(.5,.85),'left':(.26,.5),'right':(.79,.5),'left_left':(.18,.14),'left_right':(.52,.14)}
for parent,child in [('root','left'),('root','right'),('left','left_left'),('left','left_right')]:
 px,py=positions[parent];cx,cy=positions[child];ax.annotate('',(cx,cy+.095),(px,py-.095),arrowprops={'arrowstyle':'->','color':'#7c8a94','lw':1.4})
texts={'root':'整数条件を外す\n(3, 1.5) ／ 上界21','left':'x2 ≤ 1\n(10/3, 1) ／ 上界20.667','right':'x2 ≥ 2\n(2, 2) ／ 上界18','left_left':'さらに x1 ≤ 3\n(3, 1) ／ 値19','left_right':'さらに x1 ≥ 4\n(4, 0) ／ 値20'}
for name,(x0,y0) in positions.items():
 w=.42 if name in ['root','left'] else .30;h=.18
 col='#fff0e5' if name=='left_right' else '#e9f1f6'
 ax.add_patch(FancyBboxPatch((x0-w/2,y0-h/2),w,h,boxstyle='round,pad=0.012',facecolor=col,edgecolor='#94a9b7',lw=1.2))
 ax.text(x0,y0,texts[name],ha='center',va='center',fontsize=9.5)
fig.suptitle('MILP：整数の候補を探す仕事と、「もっと良い解がない」と示す仕事',fontsize=14)
for ext in ['svg','png']:fig.savefig(P/'media'/f'milp-relaxation-tree.{ext}',dpi=180)
plt.close(fig)
report={'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'milp':{'x':integer.x.tolist(),'profit':float(-integer.fun),'status':int(integer.status),'success':bool(integer.success),'mip_gap':float(integer.mip_gap),'mip_dual_bound_minimization':float(integer.mip_dual_bound),'solver_reported_nodes':int(integer.mip_node_count)},'enumerated_points':points.tolist(),'manual_lp_tree_depth_first_order':nodes,'final_leaf_upper_bound':20,'root_relative_gap_with_incumbent_20':.05,'rounding':{'up':[3,2],'constraint_excess':[2,1],'down':[3,1],'down_profit':19},'big_m_example':bigm,'tests':'all assertions passed','limit':'The five manually chosen LP nodes are not a HiGHS search log.'}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
