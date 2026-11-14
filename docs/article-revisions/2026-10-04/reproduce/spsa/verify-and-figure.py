from pathlib import Path
import json,platform,itertools,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/compass-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/compass-cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parent
FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':FONT.get_name(),'font.size':11,'svg.fonttype':'path'})
def f(x):return float(np.sum((x-1)**2))
def estimate(x,delta,c=.1):
    yp=f(x+c*delta);ym=f(x-c*delta)
    return yp,ym,(yp-ym)/(2*c*delta)
def noisy_twenty(seed):
    rng=np.random.default_rng(seed);x=np.zeros(20)
    for k in range(1,101):
        delta=rng.choice(np.array([-1.,1.]),size=x.shape);a=.1/k**.602;c=.1/k**.101
        yp=f(x+c*delta)+.01*rng.normal();ym=f(x-c*delta)+.01*rng.normal()
        x-=a*(yp-ym)/(2*c*delta)
    noisy_final=f(x)+.01*rng.normal()
    return {'seed':seed,'x_first3':x[:3].tolist(),'exact_diagnostic':f(x),'noisy_final':noisy_final,'noisy_oracle_calls':201,'exact_diagnostic_evaluations':1}
def main():
    x=np.zeros(2);rows=[]
    for k,d in enumerate([[1,1],[1,-1],[1,1]],1):
        d=np.array(d);before=x.copy();yp,ym,g=estimate(x,d);x-=.1*g
        rows.append({'update':k,'before':before.tolist(),'delta':d.tolist(),'y_plus':yp,'y_minus':ym,'estimate':g.tolist(),'after':x.tolist(),'objective':f(x)})
    assert np.allclose([r['objective'] for r in rows],[.72,.72,.2592])
    x0=np.array([.4,.4]);dirs=np.array(list(itertools.product([-1.,1.],repeat=2)))
    est=np.array([estimate(x0,d)[2] for d in dirs]);true=2*(x0-1)
    assert np.allclose(est.mean(axis=0),true)
    assert np.allclose(est.var(axis=0),[1.44,1.44])
    assert np.linalg.norm(true)>1 and np.allclose(est[1],0)
    noisy=[noisy_twenty(s) for s in range(30)]
    vals=np.array([r['exact_diagnostic'] for r in noisy])
    out={'environment':{'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__},'main_rows':rows,'main_update_calls':6,'main_diagnostic_calls':3,
         'all_four_at_point_0_4':{'point':x0.tolist(),'deltas':dirs.tolist(),'estimates':est.tolist(),'mean':est.mean(axis=0).tolist(),'true_gradient':true.tolist(),'component_variance':est.var(axis=0).tolist(),'enumeration_calls':8},
         'noise_variance_formula':'sigma^2/(2*c^2), independent equal-variance +/- observations',
         'fixed_seed_supplement':noisy[7],'supplement_seeds_0_to_29':{'exact_final_quantiles_0_25_50_75_100':np.quantile(vals,[0,.25,.5,.75,1]).tolist(),'per_run_noisy_oracle_calls':201,'per_run_exact_diagnostic_evaluations':1,'runs':noisy},'assertions':'passed'}
    (ROOT/'verified-numbers.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    fig,axs=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    a=np.linspace(-.1,1.5,250);xx,yy=np.meshgrid(a,a);zz=(xx-1)**2+(yy-1)**2
    ax=axs[0];ax.contour(xx,yy,zz,levels=[.08,.32,.72,1.28,2],colors='#d2dfe5')
    ax.plot([.3,.5],[.5,.3],'o--',color='#166e99',label='Δ=(1,−1) の正負2点')
    ax.scatter([.4],[.4],color='#253746',s=60,zorder=5)
    ax.annotate('現在点 (0.4,0.4)',(.4,.4),xytext=(-.02,.13),arrowprops={'arrowstyle':'->','color':'#536976'})
    ax.annotate('どちらも f=0.74',(.3,.5),xytext=(-.03,.96),arrowprops={'arrowstyle':'->','color':'#166e99'})
    ax.annotate('',xy=(.88,.88),xytext=(.4,.4),arrowprops={'arrowstyle':'->','lw':2.5,'color':'#c46b22'})
    ax.text(.69,.70,'真の下降方向',rotation=45,color='#a75111')
    ax.scatter([1],[1],marker='*',s=140,color='#253746',label='最小点 (1,1)')
    ax.set(xlim=(-.05,1.35),ylim=(-.05,1.35),xlabel='x1',ylabel='x2',title='A. 2回目：推定0でも、最小点ではない');ax.set_aspect('equal');ax.legend(loc='lower right',fontsize=9)
    ax=axs[1];pos=np.arange(4);ax.bar(pos,est[:,0],color=['#166e99','#a8bac4','#a8bac4','#166e99'])
    ax.axhline(true[0],color='#c46b22',lw=2,label='4方向の平均 = 真の勾配成分 −1.2')
    ax.set(xticks=pos,xticklabels=['(−1,−1)','(−1,1)','(1,−1)','(1,1)'],ylim=(-2.75,.3),ylabel='推定勾配の第1成分',xlabel='摂動方向 Δ',title='B. 4通りの平均は、真の勾配と一致');ax.legend(loc='lower center',fontsize=9);ax.grid(axis='y',alpha=.15)
    for k,v in enumerate(est[:,0]):ax.text(k,v-.12 if v<0 else .06,f'{0. if abs(v)<1e-12 else v:.1f}',ha='center')
    fig.suptitle('SPSA：2評価で得るのは、揺らぐ勾配の推定',fontsize=16)
    (ROOT/'media').mkdir(exist_ok=True)
    for ext in ['svg','png']:fig.savefig(ROOT/'media'/f'spsa-two-evaluations.{ext}',dpi=180)
    print(json.dumps({k:v for k,v in out.items() if k!='supplement_seeds_0_to_29'},ensure_ascii=False,indent=2))
    print('30-seed quantiles:',np.quantile(vals,[0,.25,.5,.75,1]))
if __name__=='__main__':main()
