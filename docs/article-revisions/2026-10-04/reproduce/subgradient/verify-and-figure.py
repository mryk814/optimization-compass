"""Reproduce the article, validate its claims, and regenerate its figure."""
from pathlib import Path
import json, platform
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parent
FONT = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': FONT.get_name(), 'font.size': 11, 'svg.fonttype': 'path'})

def objective(p):
    return float(abs(p[0]-1) + 20*abs(p[1]+2))

def subgradient(p):
    return np.array([np.sign(p[0]-1), 20*np.sign(p[1]+2)])

def run(step, iterations=1000):
    p=np.array([4.,3.]); rows=[]; best=objective(p)
    for k in range(iterations):
        f=objective(p); best=min(best,f)
        rows.append([k,*p,f,best])
        p=p-step(k)*subgradient(p)
    return np.array(rows)

def main():
    r=run(lambda k:1/np.sqrt(k+1)); fixed=run(lambda k:1.)
    assert np.allclose(r[:2,3],[103,302])
    assert np.all(np.diff(r[:,4])<=0)
    assert np.isclose(r[-1,4],1.6159782813662815e-5)
    assert fixed[-1,4] == 100
    # Subgradient support inequality on a deterministic grid, including kinks.
    gap=[]
    for p in (np.array([4.,3.]),np.array([1.,-2.]),np.array([4.,-2.])):
        for q in np.array(np.meshgrid(np.linspace(-3,5,11),np.linspace(-4,4,11))).reshape(2,-1).T:
            gap.append(objective(q)-objective(p)-subgradient(p)@(q-p))
    assert min(gap)>-1e-12
    p=np.array([4.,-2.]); g=np.array([1.,20.]); a=.001
    ascent=objective(p-a*g)-objective(p)
    assert np.isclose(ascent,399*a)
    alpha=1/np.sqrt(np.arange(1,1001))
    bound=(34+401*np.sum(alpha**2))/(2*np.sum(alpha))
    out={'environment':{'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__},
         'initial':[4,3], 'optimum':[1,-2], 'step':'1/sqrt(k+1)',
         'first_seven':[{'k':int(k),'p':[x,y],'value':f,'best':b} for k,x,y,f,b in r[:7]],
         'sampled_iterates':'k=0,...,999; x_1000 is updated but not evaluated',
         'best_of_1000_evaluated_points':r[-1,4], 'fixed_step_best':fixed[-1,4],
         'kink_non_descent':{'p':p.tolist(),'g':g.tolist(),'alpha':a,'objective_increase':ascent},
         'G_squared':401,'R_squared':34,'bound_at_T_1000':bound,
         'minimum_sampled_support_gap':min(gap),'assertions':'passed'}
    (ROOT/'verified-numbers.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    ax=axes[0]; ax.axhline(-2,color='#839496',lw=1);ax.axvline(1,color='#839496',lw=1)
    ax.plot(r[:7,1],r[:7,2],'-o',color='#196d9a',lw=2)
    for k,x,y,*_ in r[:7]: ax.annotate(str(int(k)),(x,y),xytext=(7,5),textcoords='offset points')
    ax.scatter([1],[-2],marker='*',s=160,color='#d26922',zorder=5,label='最小点 (1, −2)')
    ax.set(xlabel='x',ylabel='y',title='A. 最初の6更新：yの折れ目を飛び越す')
    ax.legend(loc='lower right'); ax.grid(alpha=.16)
    ax=axes[1]; ax.semilogy(r[:101,0],r[:101,3],color='#196d9a',alpha=.75,label='現在値')
    ax.semilogy(r[:101,0],r[:101,4],color='#d26922',lw=2.7,label='これまでの最良値')
    ax.set(xlabel='評価した点の番号 k',ylabel='目的値（対数目盛）',title='B. 下がり続けるのは「記録」')
    ax.legend(); ax.grid(alpha=.16)
    fig.suptitle('劣勾配法：同じ一手で、目的値は上がりうる',fontsize=16)
    (ROOT/'media').mkdir(exist_ok=True)
    for ext in ['svg','png']: fig.savefig(ROOT/'media'/f'subgradient-record.{ext}',dpi=180)
    plt.close(fig)
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
