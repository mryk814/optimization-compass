"""Exact tableau calculations and independent cold-start HiGHS checks."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/discrete-mpl')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/discrete-cache')
from pathlib import Path
from fractions import Fraction as F
import json, platform, copy
import numpy as np
import scipy
from scipy.optimize import linprog
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
P=Path(__file__).resolve().parent
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'font.size':11,'svg.fonttype':'path'})
root_rows=[[F(1),F(0),F(1,4),F(-1,2),F(3)],[F(0),F(1),F(-1,8),F(3,4),F(3,2)]]
root_cost=[F(0),F(0),F(3,4),F(1,2),F(21)]

def branch(rows,cost,basis,names,coefs,rhs,new_name):
    rows=[r[:-1]+[F(0),r[-1]] for r in rows]
    cost=cost[:-1]+[F(0),cost[-1]]
    n=len(names)+1;names=names+[new_name];basis=list(basis)
    new=list(map(F,coefs))+[F(0)]*(n-len(coefs)-1)+[F(1),F(rhs)]
    for b,r in zip(basis,rows):
        f=new[b];new=[a-f*v for a,v in zip(new,r)]
    rows.append(new);basis.append(n-1)
    before={'rows':copy.deepcopy(rows),'cost':list(cost),'basis':list(basis)}
    trace=[]
    while any(r[-1]<0 for r in rows):
        assert all(v>=0 for v in cost[:-1])
        r=min(range(len(rows)),key=lambda i:rows[i][-1])
        candidates=[j for j in range(n) if rows[r][j]<0]
        if not candidates:raise ValueError('infeasible')
        j=min(candidates,key=lambda j:cost[j]/-rows[r][j])
        ratio=cost[j]/-rows[r][j]
        trace.append({'leaving':names[basis[r]],'entering':names[j],'rhs':str(rows[r][-1]),'ratio':str(ratio)})
        p=rows[r][j];rows[r]=[v/p for v in rows[r]]
        for i in range(len(rows)):
            if i!=r:
                f=rows[i][j];rows[i]=[a-f*v for a,v in zip(rows[i],rows[r])]
        f=cost[j];cost=[a-f*v for a,v in zip(cost,rows[r])];basis[r]=j
    assert all(v>=0 for v in cost[:-1]);assert all(r[-1]>=0 for r in rows)
    sol=[F(0)]*n
    for b,r in zip(basis,rows):sol[b]=r[-1]
    assert 5*sol[0]+4*sol[1]==cost[-1]
    return rows,cost,basis,names,sol,trace,before
r1=branch(root_rows,root_cost,[0,1],['x1','x2','s1','s2'],[0,1],1,'t')
r2=branch(root_rows,root_cost,[0,1],['x1','x2','s1','s2'],[0,-1],-2,'u')
r3=branch(*r1[:4],[1,0],3,'v')
r4=branch(*r1[:4],[-1,0],-4,'w')
results=[]
for label,r,con,b in [('x2 <= 1',r1,[[0,1]],[1]),('x2 >= 2',r2,[[0,-1]],[-2]),('x2 <= 1; x1 <= 3',r3,[[0,1],[1,0]],[1,3]),('x2 <= 1; x1 >= 4',r4,[[0,1],[-1,0]],[1,-4])]:
    rows,cost,basis,names,sol,trace,before=r
    A=[[6,4],[1,2]]+con;rhs=[24,6]+b
    check=linprog([-5,-4],A_ub=A,b_ub=rhs,bounds=(0,None),method='highs-ds')
    assert check.success and np.allclose(check.x,[float(s) for s in sol[:2]])
    assert abs(-check.fun-float(cost[-1]))<1e-10
    results.append({'branch':label,'exact_solution':[str(s) for s in sol[:2]],'objective':str(cost[-1]),'trace':trace,'basis':[names[b] for b in basis],'rows':[[str(x) for x in z] for z in rows],'rho':[str(x) for x in cost[:-1]],'scipy_status':check.status,'scipy_objective':-check.fun})
assert results[0]['objective']=='62/3';assert all(len(r['trace'])==1 for r in results)
# Explicit nonnegative dual certificate for max c*x, A*x<=b.
y=[F(5,6),F(0),F(2,3)];A=[[6,4],[1,2],[0,1]];b=[24,6,1]
assert [sum(y[i]*A[i][j] for i in range(3)) for j in range(2)]==[5,4]
assert sum(a*v for a,v in zip(y,b))==F(62,3)
fig,(ax,at)=plt.subplots(1,2,figsize=(12,4.8),gridspec_kw={'width_ratios':[1.05,1]},layout='constrained')
root=np.array([[0,0],[4,0],[3,1.5],[0,3]])
child=np.array([[0,0],[4,0],[10/3,1],[0,1]])
ax.fill(*root.T,color='#dee7ed',label='追加前の可行領域');ax.fill(*child.T,color='#b9ddd4',label='追加後の可行領域')
xx=np.linspace(0,4.5,100)
ax.plot(xx,(24-6*xx)/4,c='#8297a7');ax.plot(xx,(6-xx)/2,c='#8297a7');ax.axhline(1,c='#cd802f',ls='--',label='追加条件 x2 ≤ 1')
ax.scatter([3,10/3],[1.5,1],c=['#c27c30','#247c69'],s=70,zorder=4)
ax.annotate('旧解 (3, 1.5)\nz = 21',xy=(3,1.5),xytext=(1.1,2.1),arrowprops={'arrowstyle':'->','color':'#52626d'})
ax.annotate('修復後 (10/3, 1)\nz = 62/3',xy=(10/3,1),xytext=(2.7,.20),arrowprops={'arrowstyle':'->','color':'#52626d'})
ax.annotate('',xy=(10/3,1),xytext=(3,1.5),arrowprops={'arrowstyle':'->','color':'#c27c30','lw':2})
ax.set(xlim=(-.05,4.4),ylim=(-.05,3.3),xlabel='x1',ylabel='x2',title='旧解は追加条件を破る');ax.legend(loc='upper right',fontsize=9)
at.axis('off');at.set_title('一回の基底交換で主可行性を回復')
table=at.table(cellText=[['x1','3','10/3'],['x2','3/2','1'],['t','−1/2（違反）','0（非基底）'],['s2','0（非基底）','2/3'],['ρ(s1)','3/4','5/6'],['ρ(s2) / ρ(t)','1/2 / 0','0 / 2/3'],['z の上界','21','62/3']],colLabels=['量','追加直後','ピボット後'],cellLoc='center',bbox=[0,.18,1,.70])
table.auto_set_font_size(False);table.set_fontsize(11)
for (i,j),cell in table.get_celld().items():
 cell.set_edgecolor('#d9e2e6');cell.set_facecolor('#e4eeef' if i==0 else ('#fff2e5' if i==3 else 'white'))
at.text(.5,.05,'入る s2 ／ 出る t\n両方で ρ ≥ 0、最後に基本変数も ≥ 0',transform=at.transAxes,ha='center',va='center',fontsize=12)
for ext in ['svg','png']:fig.savefig(P/f'dual-simplex-one-pivot.{ext}',dpi=180)
report={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'convention':'max; rows x_B + alpha*x_N=b; z+rho*x_N=z0; rho = c_B B^-1 A_N-c_N = -standard_reduced_cost','branch_results':results,'dual_certificate':{'y':[str(v) for v in y],'A_transpose_y':[5,4],'dual_objective':'62/3'},'scipy_is_cold_start_crosscheck':True,'basis_warm_start_benchmark_executed':False}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'branches':[(r['branch'],r['objective']) for r in results],'dual':'62/3'},ensure_ascii=False))
