from pathlib import Path
import json,platform,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/compass-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/compass-cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parent
FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':FONT.get_name(),'font.size':11,'svg.fonttype':'path'})
def run(eta=.1,beta=.5,n=16):
    x=2.;v=0.;rows=[]
    for k in range(1,n+1):
        g=2*(x-1);carry=beta*v;v=carry+g;x=x-eta*v
        rows.append({'update':k,'gradient':g,'carry':carry,'velocity':v,'x':x,'objective':(x-1)**2})
    return rows
def main():
    rows=run();r=np.array([[v['x'],v['gradient'],v['carry'],v['velocity']] for v in rows])
    assert np.allclose(r[:3,0],[1.8,1.54,1.302])
    x=np.r_[2,r[:,0]];e=x-1
    assert np.allclose(e[2:],1.3*e[1:-1]-.5*e[:-2])
    roots=np.roots([1,-1.3,.5]); assert np.allclose(abs(roots),np.sqrt(.5))
    assert rows[5]['x']<1 and rows[5]['objective']>rows[4]['objective']
    # Existing 2-D example, preserved separately.
    z=np.array([4.,3.]);v=np.zeros(2)
    for k in range(2000):
        g=np.array([2*(z[0]-1),80*(z[1]+2)]);v=.85*v+g;z-=.02*v
        if np.linalg.norm([2*(z[0]-1),80*(z[1]+2)])<1e-8 and np.linalg.norm(v)<1e-8: break
    out={'environment':{'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__},'eta':.1,'beta':.5,'initial_x':2,'initial_velocity':0,'first_eight':rows[:8],
         'characteristic_roots':[{'real':float(a.real),'imag':float(a.imag),'abs':float(abs(a))} for a in roots],
         'stable_eta_range_for_h2_beta_half':'0 < eta < 1.5',
         'supplement_2d':{'updates':k+1,'x':z.tolist(),'objective':float((z[0]-1)**2+40*(z[1]+2)**2),'gradient_norm':float(np.linalg.norm([2*(z[0]-1),80*(z[1]+2)]))},'assertions':'passed'}
    (ROOT/'verified-numbers.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    ax=axs[0];ax.axhline(1,color='#78909c',lw=1,label='最小点 x=1')
    ax.plot(range(len(x)),x,'o-',color='#166e99',label='Momentum');ax.plot(range(len(x)),1+.8**np.arange(len(x)),'--',color='#c46b22',label='勾配降下（同じ η）')
    ax.annotate('6回目で最小点を通過',xy=(6,x[6]),xytext=(7,1.45),arrowprops={'arrowstyle':'->','color':'#555'})
    ax.set(xlabel='更新数',ylabel='x',title='A. 勾配が弱くなっても、速度が残る');ax.legend();ax.grid(alpha=.18)
    ax=axs[1];ks=np.arange(1,9);g=r[:8,1];carry=r[:8,2]
    ax.bar(ks-.16,g,.32,color='#166e99',label='現在の勾配 g')
    ax.bar(ks+.16,carry,.32,color='#c46b22',label='持越し βv')
    ax.plot(ks,r[:8,3],'k.-',label='合計 v（次の更新状態）')
    ax.axhline(0,color='#78909c');ax.set(xlabel='更新番号',ylabel='勾配 / 更新状態',title='B. 符号が変わっても即座には止まらない');ax.legend(fontsize=9);ax.grid(alpha=.18)
    fig.suptitle('Momentum：現在の勾配 + 持ち越した勾配',fontsize=16)
    (ROOT/'media').mkdir(exist_ok=True)
    for ext in ['svg','png']:fig.savefig(ROOT/'media'/f'momentum-carry-step.{ext}',dpi=180)
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
