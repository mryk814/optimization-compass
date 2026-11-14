"""Enumerate 81 assignments; optionally run CP-SAT only if already installed."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/discrete-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/discrete-cache')
from itertools import product
from pathlib import Path
import importlib.util,json,platform
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
P=Path(__file__).resolve().parent
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'font.size':11,'svg.fonttype':'path'})
cost=[[3,8,4,6],[5,2,7,3],[6,4,3,5]];capacity=[2,2,2]
rows=[]
for a in product(range(3),repeat=4):
 counts=[a.count(w) for w in range(3)]
 value=sum(cost[a[t]][t] for t in range(4))
 rows.append({'assignment':list(a),'counts':counts,'cost':value,'feasible':all(n<=c for n,c in zip(counts,capacity))})
feasible=[r for r in rows if r['feasible']];best=min(feasible,key=lambda r:r['cost'])
bound=sum(min(cost[w][t] for w in range(3)) for t in range(4))
assert len(rows)==81 and best['cost']==11 and bound==11
assert best['assignment']==[0,1,2,1]
for a,v,f in [([0,0,0,0],21,False),([0,1,0,1],12,True),([0,1,2,1],11,True)]:
 r=next(r for r in rows if r['assignment']==a);assert (r['cost'],r['feasible'])==(v,f)
cp={'executed':False,'reason':'ortools is not installed; no install attempted','status':None,'objective':None,'best_objective_bound':None}
if importlib.util.find_spec('ortools') is not None:
 import ortools
 from ortools.sat.python import cp_model
 model=cp_model.CpModel();x={(w,t):model.new_bool_var(f'x_{w}_{t}') for w in range(3) for t in range(4)}
 for t in range(4):model.add(sum(x[w,t] for w in range(3))==1)
 for w in range(3):model.add(sum(x[w,t] for t in range(4))<=capacity[w])
 model.minimize(sum(cost[w][t]*x[w,t] for w in range(3) for t in range(4)))
 solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=10;solver.parameters.random_seed=7;solver.parameters.num_search_workers=1
 status=solver.solve(model)
 cp={'executed':True,'version':ortools.__version__,'status':solver.status_name(status)}
 if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
  cp.update(objective=solver.objective_value,best_objective_bound=solver.best_objective_bound)
  assert abs(solver.objective_value-11)<1e-9
fig,axes=plt.subplots(1,3,figsize=(12.5,4.7),layout='constrained')
for ax,ass,title in zip(axes,[[0,0,0,0],[0,1,0,1],[0,1,2,1]],['容量違反：候補から除く','可行：費用12','最適：費用11 = 下界11']):
 r=next(r for r in rows if r['assignment']==ass)
 values=np.zeros((3,4))
 for t,w in enumerate(ass):values[w,t]=1
 from matplotlib.colors import ListedColormap
 ax.imshow(values,cmap=ListedColormap(['#f0f3f4','#cae5db']),vmin=0,vmax=1)
 for w in range(3):
  for t in range(4):
   ax.text(t,w,str(cost[w][t]),ha='center',va='center',fontsize=15,fontweight='bold' if ass[t]==w else 'normal',color='#155d4f' if ass[t]==w else '#7c8b92')
 ax.set_xticks(range(4),[f'仕事{t}' for t in range(4)]);ax.set_yticks(range(3),[f'人{w}' for w in range(3)])
 ax.set_title(title,pad=16,fontsize=12);ax.set_xticks(np.arange(-.5,4,1),minor=True);ax.set_yticks(np.arange(-.5,3,1),minor=True);ax.grid(which='minor',color='white',linewidth=3);ax.tick_params(which='both',length=0)
 ax.text(.5,-.20,'担当数 '+str(tuple(r['counts']))+' ／ 容量 (2, 2, 2)',ha='center',transform=ax.transAxes,fontsize=10)
 ax.text(.5,-.32,'担当 '+str(tuple(ass)),ha='center',transform=ax.transAxes,fontsize=10)
fig.suptitle('色の付いたセルが担当：数字は人×仕事の費用',fontsize=15,fontweight='bold')
for ext in ['svg','png']:fig.savefig(P/f'cp-sat-assignment-oracle.{ext}',dpi=180)
report={'python':platform.python_version(),'numpy':np.__version__,'total_assignments':len(rows),'feasible_assignments':len(feasible),'infeasible_assignments':len(rows)-len(feasible),'optimal_assignments':[r for r in feasible if r['cost']==11],'manual_relaxation_lower_bound':bound,'cp_sat':cp,'all_assignments':rows,'figure_is_internal_solver_trace':False}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['total_assignments','feasible_assignments','infeasible_assignments','optimal_assignments','cp_sat']},ensure_ascii=False))
