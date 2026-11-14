from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/optimization-compass-mpl')
import numpy as np,scipy,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from scipy.optimize import differential_evolution
OUT=Path(__file__).parent
MEDIA=OUT/'media';MEDIA.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name(),'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path'})
f=lambda x:float((x[0]-1)**2+(x[1]-2)**2)
rng=np.random.default_rng(7);pop=rng.uniform(-5,5,(8,2));values=np.array([f(x) for x in pop]);initial=pop.copy();records=[]
def summary(gen,replaced):return {'generation':gen,'nfev':8*(gen+1),'min':float(values.min()),'mean':float(values.mean()),'rms_spread':float(np.sqrt(np.mean(np.sum((pop-pop.mean(0))**2,axis=1)))),'replaced':replaced,'population':pop.tolist(),'values':values.tolist()}
summaries=[summary(0,0)]
for generation in range(1,4):
 newpop=pop.copy();newvalues=values.copy();replaced=0
 for i in range(8):
  others=[j for j in range(8) if j!=i];idx=rng.choice(others,3,replace=False);r1,r2,r3=idx
  assert len(set([i,*idx]))==4
  raw=pop[r1]+.5*(pop[r2]-pop[r3]);mutant=np.clip(raw,-5,5)
  draws=rng.random(2);mask=draws<.9;forced=int(rng.integers(2));mask[forced]=True
  trial=np.where(mask,mutant,pop[i]);value=f(trial);accepted=bool(value<=values[i]);assert mask.any();assert np.all((-5<=trial)&(trial<=5))
  records.append({'generation':generation,'target_index':i,'target':pop[i].tolist(),'target_f':float(values[i]),'donor_indices':idx.tolist(),'donors':pop[idx].tolist(),'raw_mutant':raw.tolist(),'clipped_mutant':mutant.tolist(),'cross_uniforms':draws.tolist(),'forced_coordinate':forced,'mask':mask.tolist(),'trial':trial.tolist(),'trial_f':value,'accepted':accepted})
  if accepted:newpop[i]=trial;newvalues[i]=value;replaced+=1
 pop,values=newpop,newvalues;summaries.append(summary(generation,replaced))
assert np.allclose([s['min'] for s in summaries],[3.0574060717143157, .5121180732784254, .3619581048161977, .3619581048161977],atol=1e-12,rtol=1e-12)
assert [s['replaced'] for s in summaries]==[0,4,5,5]
a=records[4];assert a['target_index']==4 and a['donor_indices']==[7,2,3] and a['accepted']
b=records[0];assert b['raw_mutant'][0]<-5 and not b['mask'][0]
# Same objective/box/population, but SciPy draws differ from the textbook loop.
lib=differential_evolution(f,[(-5,5),(-5,5)],strategy='rand1bin',init=initial,mutation=.5,recombination=.9,maxiter=3,polish=False,updating='deferred',workers=1,rng=7)
assert lib.nfev==32
fig,axes=plt.subplots(1,3,figsize=(14,4.9),layout='constrained')
ax=axes[0];don=np.array(a['donors']);mut=np.array(a['clipped_mutant']);x=np.array(a['target'])
ax.scatter(initial[:,0],initial[:,1],c='#cbd3de',s=30)
for label,point,col,offset in zip(['r1=7','r2=2','r3=3'],don,['#2f5b95','#168879','#168879'],[(8,-17),(8,7),(8,-17)]):
 ax.scatter(*point,c=col,s=65);ax.annotate(label,point,xytext=offset,textcoords='offset points')
ax.annotate('',xy=don[1],xytext=don[2],arrowprops={'arrowstyle':'->','color':'#168879','lw':2})
ax.annotate('',xy=mut,xytext=don[0],arrowprops={'arrowstyle':'->','color':'#bf543b','lw':2})
ax.scatter(*mut,marker='X',s=95,c='#bf543b');ax.annotate('変異 v4',mut,xytext=(8,7),textcoords='offset points')
ax.scatter(1,2,marker='*',s=120,color='#18334f',label='解析解 (1, 2)')
ax.set(xlim=(-5.5,4),ylim=(-3.5,4.6),xlabel='x1',ylabel='x2',title='1. 差分を半分にして r1 に足す');ax.legend(fontsize=9,loc='lower left')
ax=axes[1];ax.bar([0,1],[a['target_f'],a['trial_f']],color=['#2f5b95','#168879'],width=.6)
for i,y in enumerate([a['target_f'],a['trial_f']]):ax.text(i,y+.2,f'{y:.3f}',ha='center')
ax.set(xticks=[0,1],xticklabels=['対象 x4','交叉後 u4 = v4'],ylabel='目的値',ylim=(0,11.5),title='2. 両座標を交叉して置換')
ax.text(.5,.94,'mask = [True, True]\n(2.971, −0.321) → (1.520, 0.797)',transform=ax.transAxes,ha='center',va='top',fontsize=10)
ax=axes[2];g=np.arange(4);ax.plot(g,[s['min'] for s in summaries],'o-',color='#168879',label='最良値');ax.plot(g,[s['mean'] for s in summaries],'s-',color='#2f5b95',label='平均値');ax.set(xticks=g,xlabel='世代（累積評価数 = 8 × (世代 + 1)）',ylabel='目的値',title='3. 最良値が同じでも集団は変わる');ax.legend(fontsize=9)
fig.suptitle('DE/rand/1/bin  |  8個体、F = 0.5、CR = 0.9、世代内は元の集団を固定',fontsize=15)
for ext in ['svg','png']:fig.savefig(MEDIA/f'differential-evolution-step.{ext}',dpi=170)
report={'numpy':np.__version__,'scipy':scipy.__version__,'type':'educational DE/rand/1/bin','rng':'default_rng(7)','population_size':8,'F':.5,'CR':.9,'boundary':'clip mutant before crossover','updating':'deferred','records':records,'summaries':summaries,'scipy_supplement':{'x':lib.x.tolist(),'fun':float(lib.fun),'nfev':lib.nfev,'success':bool(lib.success),'message':lib.message},'oracle':{'x':[1,2],'f':0},'tests':'passed'}
(OUT/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'target4':a,'summary':summaries,'scipy':report['scipy_supplement']},ensure_ascii=False,indent=2))
