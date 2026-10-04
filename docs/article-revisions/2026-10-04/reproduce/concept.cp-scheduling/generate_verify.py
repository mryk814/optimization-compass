"""Reproduce the article's complete ordering oracle and its figure; not CP-SAT."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/discrete-mpl')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/discrete-cache')
from pathlib import Path
from itertools import permutations, product
import json, platform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
P=Path(__file__).resolve().parent
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'font.size':12,'svg.fonttype':'path'})
duration={'A':2,'B':3,'C':1}
release={'A':0,'B':4,'C':0}
rows=[]
for order in permutations(duration):
    if order.index('A')>order.index('C'): continue
    start={};clock=0
    for task in order:
        clock=max(clock,release[task]);start[task]=clock;clock+=duration[task]
    rows.append({'order':list(order),'starts':start,'makespan':clock})
assert [r['makespan'] for r in rows]==[8,7,10]
# Independent bounded start-time oracle. A known feasible schedule has makespan 7,
# so all strictly better integer starts lie in 0..6. Search 0..10 as a cross-check.
feasible=[]
for starts in product(range(11),repeat=3):
    s=dict(zip(duration,starts))
    if any(s[k]<release[k] for k in s) or s['C']<s['A']+duration['A']:continue
    if any(not(s[a]+duration[a]<=s[b] or s[b]+duration[b]<=s[a]) for a,b in [('A','B'),('A','C'),('B','C')]):continue
    end=max(s[k]+duration[k] for k in s)
    feasible.append((end,s))
assert min(x[0] for x in feasible)==7
best=min(rows,key=lambda x:x['makespan'])
assert best['makespan']==release['B']+duration['B']==7
variation=[]
for order in [('A','B','C'),('A','C','B')]:
    clock=0
    for task in order:
        clock=max(clock,2 if task=='B' else 0)+duration[task]
    variation.append(clock)
assert variation==[6,6]

fig,ax=plt.subplots(figsize=(11.5,4.5),layout='constrained')
colors={'A':'#387ca4','B':'#d58932','C':'#38968b'}
for y,r in enumerate(rows):
    for k in r['order']:
        s=r['starts'][k];w=duration[k]
        ax.barh(y,w,left=s,height=.54,color=colors[k],edgecolor='white')
        ax.text(s+w/2,y,f'{k}  [{s},{s+w})',va='center',ha='center',color='white',fontsize=12,fontweight='bold')
    ax.text(r['makespan']+.14,y,f"終了 {r['makespan']}",va='center')
ax.axvspan(3,4,ymin=.34,ymax=.66,color='#e9edf1',zorder=0)
ax.axvline(4,color='#b4772d',ls=':',lw=1.5)
ax.axvline(7,color='#398071',ls='--',lw=1.5)
ax.text(4,1.02,'B は時刻4から',transform=ax.get_xaxis_transform(),ha='center',color='#925d21')
ax.text(7,1.02,'下界 = 4 + 3 = 7',transform=ax.get_xaxis_transform(),ha='center',color='#246b60')
ax.set_yticks(range(3),['A → B → C','A → C → B','B → A → C'])
ax.invert_yaxis();ax.set_xlim(0,11.6);ax.set_xticks(range(12));ax.set_xlabel('時刻');ax.set_title('一台・中断なし：順序を固定して最も早く開始する',loc='left',pad=42,fontweight='bold');ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
for s in ['top','right','left']:ax.spines[s].set_visible(False)
for ext in ['svg','png']:fig.savefig(P/f'cp-scheduling-order-oracle.{ext}',dpi=180)
report={'python':platform.python_version(),'matplotlib':matplotlib.__version__,'model':'one machine, nonpreemptive, integer durations/releases, A precedes C','total_orders':6,'precedence_feasible_orders':len(rows),'rows':rows,'release_lower_bound':7,'release_B_2_variation_makespans':variation,'best':best,'start_grid_oracle':{'domain':'each start 0..10','candidates':11**3,'minimum_makespan':min(x[0] for x in feasible)},'cp_sat_executed':False,'claims':['The sequence enumeration is an exact oracle for this fixed one-machine model. It does not represent CP-SAT search order.','Integer oracle alone does not prove continuous-time optimality; B release plus duration does.']}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'orders':len(rows),'best':best,'lower_bound':7},ensure_ascii=False))
