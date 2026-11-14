from pathlib import Path
import json,platform,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/compass-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/compass-cache')
import numpy as np
import scipy
from scipy.optimize import linprog
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parent
FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':FONT.get_name(),'font.size':11,'svg.fonttype':'path'})
B=np.array([[3.,2.],[1.,3.]])
A=np.c_[B,np.eye(2)];b=np.array([18.,13.]);c=np.array([-3.,-4.,0.,0.])
def central(mu,start=None):
    u=np.array([2.,2.]) if start is None else start.copy()
    def phi(u):
        z=np.r_[u,b-B@u]
        return c[:2]@u-mu*np.log(z).sum() if np.all(z>0) else np.inf
    for k in range(100):
        slack=b-B@u;g=c[:2]-mu/u+mu*B.T@(1/slack)
        H=np.diag(mu/u**2)+mu*B.T@np.diag(1/slack**2)@B
        p=np.linalg.solve(H,-g)
        if np.linalg.norm(g,np.inf)<1e-10:break
        alpha=1.;old=phi(u)
        while phi(u+alpha*p)>old+.01*alpha*g@p:
            alpha*=.5
            if alpha<1e-14:raise RuntimeError('central line search stalled')
        u+=alpha*p
    x=np.r_[u,b-B@u];s=mu/x;y=-s[2:]
    rp=A@x-b;rd=A.T@y+s-c
    assert np.max(abs(rd))<1e-8 and np.max(abs(rp))<1e-10
    return {'mu':mu,'x':x.tolist(),'y':y.tolist(),'s':s.tolist(),'revenue':float(-c@x),'objective_gap_to_optimum':float(24+c@x),'dual_gap':float(c@x-b@y),'complementarity':float(x@s),'primal_residual':float(np.linalg.norm(rp)),'dual_residual':float(np.linalg.norm(rd)),'centrality_residual':float(np.max(abs(x*s-mu))),'iterations':k}
def infeasible():
    x=np.ones(4);y=np.zeros(2);s=np.ones(4);rows=[]
    for k in range(9):
        rp=A@x-b;rd=A.T@y+s-c;mu=x@s/4
        rows.append({'k':k,'x':x.tolist(),'y':y.tolist(),'s':s.tolist(),'revenue':float(-c@x),'objective_difference':float(c@x-b@y),'complementarity':float(x@s),'primal_residual':float(np.linalg.norm(rp)),'dual_residual':float(np.linalg.norm(rd)),'mu':float(mu)})
        assert x.min()>0 and s.min()>0
        assert np.isclose(c@x-b@y,x@s-x@rd+y@rp)
        rc=x*s-.3*mu;d=x/s
        rhs=-rp-A@((-rc+x*rd)/s)
        dy=np.linalg.solve(A@(d[:,None]*A.T),rhs);ds=-rd-A.T@dy;dx=(-rc-x*ds)/s
        assert np.allclose(A@dx,-rp)
        assert np.allclose(A.T@dy+ds,-rd)
        assert np.allclose(s*dx+x*ds,-rc)
        step=1.
        for v,dv in [(x,dx),(s,ds)]:
            mask=dv<0
            if mask.any():step=min(step,.99*float(np.min(-v[mask]/dv[mask])))
        rows[-1]['step']=step
        x+=step*dx;y+=step*dy;s+=step*ds
    return rows
def main():
    centers=[central(mu) for mu in [10,1,.1,.01]];rows=infeasible()
    result=linprog(c[:2],A_ub=B,b_ub=b,bounds=[(0,None)]*2,method='highs-ipm')
    assert result.success and np.allclose(result.x,[4,3]) and np.isclose(result.fun,-24)
    for r in centers:
        assert np.isclose(r['dual_gap'],4*r['mu'],rtol=1e-7)
        assert 0<=r['objective_gap_to_optimum']<=r['dual_gap']+1e-8
    out={'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'central_path':centers,'infeasible_start':rows,
         'linprog_highs_ipm':{'x':result.x.tolist(),'objective':float(result.fun),'status':int(result.status),'message':result.message,'nit':int(result.nit),'crossover_nit':int(result.crossover_nit)},'assertions':'passed'}
    (ROOT/'verified-numbers.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    # Dense exact central path, never joined to the infeasible-start iterations.
    dense=np.array([central(float(mu))['x'][:2] for mu in np.geomspace(30,.01,80)])
    fig,axs=plt.subplots(1,2,figsize=(12,5.1),layout='constrained')
    ax=axs[0];poly=np.array([[0,0],[6,0],[4,3],[0,13/3],[0,0]])
    ax.fill(*poly.T,facecolor='#eff6f8',edgecolor='#809ba8');ax.plot(*dense.T,color='#166e99',lw=2,label='各 μ の中心点')
    offsets=[(-45,-28),(-63,-32),(-25,-62),(20,10)]
    for r,ofs in zip(centers,offsets):
        u=r['x'][:2];ax.scatter(*u,color='#166e99',s=40)
        ax.annotate('μ='+str(r['mu']),u,xytext=ofs,textcoords='offset points',arrowprops={'arrowstyle':'-','color':'#536976'},fontsize=10)
    ax.scatter([4],[3],marker='*',s=190,color='#c46b22',label='最適点 (4,3)',zorder=5)
    ax.set(xlim=(-.3,6.5),ylim=(-.3,4.75),xlabel='x1',ylabel='x2',title='A. 可行な中心パスだけを描く');ax.legend(loc='lower left');ax.set_aspect('equal');ax.grid(alpha=.13)
    ax=axs[1];ks=[r['k'] for r in rows]
    for key,label,col in [('primal_residual','主残差 ||Ax−b||','#166e99'),('dual_residual','双対残差 ||A^Ty+s−c||','#719540'),('complementarity','相補性 x^Ts','#c46b22')]:
        ax.semilogy(ks,[max(r[key],1e-15) for r in rows],'o-',color=col,label=label)
    ax.set(xlabel='別実験のNewton更新数',ylabel='大きさ（対数目盛）',ylim=(1e-16,50),title='B. 非可行初期点：残差も同時に確認');ax.legend(fontsize=10);ax.grid(alpha=.15)
    ax.text(.98,.20,'1e-15 未満は表示のため下限で切る',transform=ax.transAxes,ha='right',fontsize=9,color='#536976')
    fig.suptitle('バリア法：中心パスと非可行開始の反復を分ける',fontsize=16)
    (ROOT/'media').mkdir(exist_ok=True)
    for ext in ['svg','png']:fig.savefig(ROOT/'media'/f'barrier-central-residuals.{ext}',dpi=180)
    print(json.dumps({'central_path':centers,'first_four_infeasible':rows[:4],'linprog':out['linprog_highs_ipm']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
