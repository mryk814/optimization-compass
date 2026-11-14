from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch
import numpy as np
P=Path(__file__).resolve().parent
font=font_manager.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'svg.fonttype':'path','axes.unicode_minus':False})
font_manager.fontManager.addfont(font.get_file())
blue='#263B53';teal='#168A86';orange='#D7762F';paper='#FCFAF6';muted='#647381'
fig=plt.figure(figsize=(4.2,7.5),dpi=120,facecolor=paper)
ax=fig.add_axes([.07,.65,.88,.31]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
ax.text(0,.96,'残す履歴',fontsize=17,color=blue,fontproperties=font)
for yy,label,old in [(.59,'2組',True),(.25,'1組',False)]:
 ax.text(0,yy+.055,label,fontsize=14,color=blue,fontproperties=font,va='center')
 for xx,txt,c,live in [(.21,'横の観測',teal,old),(.60,'縦の観測',orange,True)]:
  ax.add_patch(FancyBboxPatch((xx,yy-.04),.34,.20,boxstyle='round,pad=.015,rounding_size=.02',facecolor=c if live else '#E6E8E7',edgecolor='none'))
  ax.text(xx+.17,yy+.06,txt,ha='center',va='center',fontsize=13,color='white' if live else '#8C969D',fontproperties=font)
 ax.text(.78,yy-.12,'新しい',ha='center',fontsize=10,color=muted,fontproperties=font)
ax.text(.38,.82,'古い',ha='center',fontsize=10,color=muted,fontproperties=font)
ax.text(.22,.015,'現在の位置は変えない',fontsize=12,color=blue,fontproperties=font)
a=fig.add_axes([.16,.14,.79,.40],facecolor=paper)
a.set_xlim(1.25,3.25);a.set_ylim(.75,3.3)
a.set_aspect('equal',adjustable='box')
a.spines[['top','right']].set_visible(False)
for sp in a.spines.values():sp.set_color('#BCC5CB')
a.tick_params(colors=muted,labelsize=10)
a.set_xticks([1.5,2,2.5,3]);a.set_yticks([1,2,3]);a.set_xlabel('x',fontsize=12,color=blue);a.set_ylabel('y',fontsize=12,color=blue,rotation=0)
a.set_title('同じ勾配から出る向き',fontsize=16,color=blue,fontproperties=font,pad=14)
d=json.loads((P/'verified-numbers.json').read_text())['frozen_history']['directions']
for m,c,label in [('0','#A4AFB7','履歴なし'),('1',orange,'1組'),('2',teal,'2組')]:
 p=np.array(d[m]['unit_p']);end=np.array([3.,3.])+2*p
 a.annotate('',xy=end,xytext=(3,3),arrowprops={'arrowstyle':'-|>','lw':2.6,'color':c,'mutation_scale':14})
 if m=='0':xy=(end[0]-.17,end[1]-.12)
 elif m=='1':xy=(end[0]-.03,end[1]+.19)
 else:xy=(end[0]-.06,end[1]-.16)
 a.text(*xy,label,color=c,fontsize=12,fontproperties=font,ha='center')
a.plot(3,3,'o',color=blue,ms=6)
a.text(2.90,3.13,'現在点 (3, 3)',ha='right',fontsize=12,color=blue,fontproperties=font)
fig.text(.5,.057,'矢印の長さは比較用に統一',ha='center',fontsize=11,color=muted,fontproperties=font)
fig.text(.5,.025,'更新後の位置や移動距離は表していません',ha='center',fontsize=10,color=muted,fontproperties=font)
(P/'media').mkdir(exist_ok=True)
fig.savefig(P/'media/lbfgs-memory-window.svg',facecolor=paper)
fig.savefig(P/'media/lbfgs-memory-window.png',facecolor=paper)
