from pathlib import Path
import math,json,platform,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/compass-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/compass-cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parent
FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':FONT.get_name(),'font.size':11,'svg.fonttype':'path'})
def run():
    x=2.;m=v=0.;rows=[]
    for k in range(1,4):
        old=x;g=2*(x-1);m=.9*m+.1*g;v=.999*v+.001*g*g
        mh=m/(1-.9**k);vh=v/(1-.999**k);step=.1*mh/(math.sqrt(vh)+1e-8);decay=.1*.1*x;x-=step+decay
        rows.append({'update':k,'before':old,'g':g,'m':m,'v':v,'mhat':mh,'vhat':vh,'gradient_step':step,'decay_step':decay,'after':x,'objective':(x-1)**2})
    return rows
def main():
    rows=run();l2g=2+.1*2;l2step=.1*l2g/(abs(l2g)+1e-8);l2x=2-l2step
    assert np.allclose([x['after'] for x in rows],[1.8800000005,1.7617351935432222,1.6456563108994302],atol=1e-12,rtol=0)
    assert np.isclose(l2x,1.9) and np.isclose(rows[0]['after'],1.88)
    out={'environment':{'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__},'convention':'loss + lambda/2 * x^2 for coupled L2; eta*lambda*x for AdamW decay','eta':.1,'lambda':.1,'betas':[.9,.999],'epsilon':1e-8,
         'rows':rows,'coupled_l2_first':{'g_data':2,'g_penalty':.2,'g_total':l2g,'m':.1*l2g,'v':.001*l2g*l2g,'mhat':l2g,'vhat':l2g*l2g,'step':l2step,'after':l2x},
         'decay_only_100_multiplier':.99**100,'assertions':'passed','framework_execution':'not run; scalar Python verified against documented PyTorch 2.8 formula'}
    (ROOT/'verified-numbers.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    fig,axs=plt.subplots(1,2,figsize=(12,5.1),layout='constrained')
    ax=axs[0];ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    def box(x,y,text,color='#edf4f7'):
        ax.text(x,y,text,ha='center',va='center',bbox={'boxstyle':'round,pad=.5','fc':color,'ec':'#6c8390'},fontsize=11)
    def arrow(a,b,c='#536976'):
        ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':c,'lw':1.8})
    ax.set_title('A. 最初の一手：同じ x=2、同じデータ勾配 2')
    box(.18,.78,'Adam + L2\ng + λx = 2.2');box(.52,.78,'m_hat = 2.2\nv_hat = 4.84');box(.86,.78,'x ≈ 1.90')
    arrow((.30,.78),(.40,.78));arrow((.64,.78),(.75,.78))
    ax.text(.51,.58,'罰則もモーメントに入る',ha='center',color='#536976')
    box(.18,.36,'AdamW\ng = 2');box(.52,.36,'m_hat = 2\nv_hat = 4');box(.86,.36,'x ≈ 1.88')
    arrow((.29,.36),(.40,.36));arrow((.63,.36),(.75,.36))
    box(.36,.13,'ηλx = 0.02','#fff1e3');arrow((.51,.13),(.86,.27),'#c46b22')
    ax.text(.78,.08,'縮小は別経路',ha='center',color='#c46b22')
    ax=axs[1];ks=np.arange(1,4);g=[r['gradient_step'] for r in rows];d=[r['decay_step'] for r in rows]
    ax.bar(ks,g,color='#166e99',label='適応的な勾配ステップ')
    ax.bar(ks,d,bottom=g,color='#c46b22',label='分離した重み減衰')
    for k,row in zip(ks,rows):ax.text(k,g[k-1]+d[k-1]+.002,f"x={row['after']:.6f}",ha='center',fontsize=10)
    ax.set(xticks=ks,ylim=(0,.15),xlabel='更新番号',ylabel='今回差し引く量',title='B. AdamWの3更新：二つの寄与を分ける');ax.legend(loc='upper right',fontsize=9);ax.grid(axis='y',alpha=.15)
    fig.suptitle('AdamW：L2罰則と「重みを縮める」は同じではない',fontsize=16)
    (ROOT/'media').mkdir(exist_ok=True)
    for ext in ['svg','png']:fig.savefig(ROOT/'media'/f'adamw-decoupled-step.{ext}',dpi=180)
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
