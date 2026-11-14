from pathlib import Path
import json
import numpy as np
from scipy.integrate import quad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'none'})
ROOT=Path(__file__).parent;MEDIA=ROOT/'site/public/media';MEDIA.mkdir(parents=True,exist_ok=True)
J=lambda m:.5*(1/m-1)**2;m=2.;rows=[]
for k in range(3):
 u=1/m;lam=(u-1)/m;g=-lam*u;h=1e-5;fd=(J(m+h)-J(m-h))/(2*h)
 assert abs(g-(m-1)/m**3)<1e-15 and abs(g-fd)<1e-9
 rows.append(dict(k=k,m=m,u=u,adjoint=lam,gradient=g,cost=J(m),fd_error=abs(g-fd)));m-=.5*g
hs=2.**(-np.arange(2,10));E0=abs(np.array([J(2+h)-J(2) for h in hs]));E1=abs(np.array([J(2+h)-J(2)-h*.125 for h in hs]));rates=np.log2(E1[:-1]/E1[1:]);assert rates[-1]>1.99
errors=[]
for residual in [1e-2,1e-3,1e-4]:
 u=(1+residual)/2;lam=(u-1)/2;err=abs(-lam*u-.125)
 assert abs(err-residual**2/8)<1e-16
 errors.append(dict(state_residual=residual,sensitivity_error=err))
# Boundary/sign sanity checks for L=J - integral lambda^T (ydot-f).
m=.2;yT=np.exp(m);lamT=yT-1
integral=quad(lambda t:lamT*np.exp(m*(1-t))*np.exp(m*t),0,1)[0]
assert abs(integral-yT*(yT-1))<1e-12
# ydot=0, y(0)=m: derivative comes solely from +lambda(0) dy0/dm.
initial_objective=lambda m:.5*(m-1.)**2
boundary_fd=(initial_objective(2.+1e-5)-initial_objective(2.-1e-5))/(2e-5)
assert abs(boundary_fd-1.)<1e-9
assert abs(boundary_fd)>0.9  # Omitting the initial boundary term would yield zero.
fig=plt.figure(figsize=(12,4.8),layout='constrained');gs=fig.add_gridspec(1,2,width_ratios=[1.4,1]);ax=fig.add_subplot(gs[0]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
boxes=[(.1,.72,'設計\nm = 2'),(.5,.72,'状態を解く\nu = 1/m = 0.5'),(.9,.72,'目的\nJ = 0.125')]
for a,b,t in boxes:ax.text(a,b,t,ha='center',va='center',bbox=dict(boxstyle='round,pad=.65',fc='#e9f2ef',ec='#128174'),fontsize=12)
for x1,x2 in [(.23,.35),(.66,.79)]:ax.annotate('',(x2,.72),(x1,.72),arrowprops=dict(arrowstyle='->',lw=2,color='#128174'))
ax.text(.55,.35,'随伴を解く\n2λ = u − 1\nλ = −0.25',ha='center',va='center',bbox=dict(boxstyle='round,pad=.6',fc='#fff0de',ec='#d47a1f'),fontsize=12)
ax.annotate('',(.68,.40),(.90,.59),arrowprops=dict(arrowstyle='->',lw=2,color='#d47a1f'))
ax.text(.12,.32,'感度を組み立てる\n−λu = +0.125',ha='center',va='center',bbox=dict(boxstyle='round,pad=.6',fc='#fff0de',ec='#d47a1f'),fontsize=12)
ax.annotate('',(.28,.34),(.4,.34),arrowprops=dict(arrowstyle='->',lw=2,color='#d47a1f'))
ax.text(.50,.07,'正の感度 → mを少し減らすとJが下がる\n更新幅を選ぶのは、別の最適化アルゴリズム',ha='center',fontsize=11)
ax.set_title('順方向で状態、逆方向で目的の感度',pad=15)
b=fig.add_subplot(gs[1]);b.loglog(hs,E0,'o-',c='#8796aa',label='一次項を引く前');b.loglog(hs,E1,'s-',c='#128174',label='一次項を引いた後');b.set_xlabel('摂動幅 h');b.set_ylabel('目的値の差 / Taylor残差');b.set_title('hを半分にすると、補正後は約1/4');b.legend();b.grid(alpha=.2)
fig.suptitle('随伴は勾配を計算する：状態 → 随伴 → 感度を分ける',fontsize=16)
for ext in ('svg','png'):fig.savefig(MEDIA/f'adjoint-scalar-chain.{ext}',dpi=160)
(ROOT/'verified-numbers.json').write_text(json.dumps({'rows':rows,'taylor_h':hs.tolist(),'taylor_remainder':E1.tolist(),'taylor_rates':rates.tolist(),'state_inexactness':errors,'continuous_adjoint_sign_check':float(integral),'initial_boundary_term_test':1.0},indent=2)+'\n')
