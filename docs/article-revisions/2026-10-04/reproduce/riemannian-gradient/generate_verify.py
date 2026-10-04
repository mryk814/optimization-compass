from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'none'})
ROOT=Path(__file__).parent;MEDIA=ROOT/'site/public/media';MEDIA.mkdir(parents=True,exist_ok=True)
A=np.diag([1.,2.]); x=np.ones(2)/np.sqrt(2);rows=[];points=[];orth=[];units=[]
for k in range(31):
 f=float(x@A@x);g=2*(A@x-f*x);rows.append([k,*x,float(f),float(np.linalg.norm(g))]);points.append(x.copy());orth.append(abs(x@g));units.append(abs(x@x-1))
 if k<30:x=(x-.25*g)/np.linalg.norm(x-.25*g)
assert max(orth)<1e-14 and max(units)<1e-14
assert abs(rows[-1][3]-np.linalg.eigvalsh(A)[0])<1e-14
angle=np.pi/4; eps=1e-6
F=lambda t: np.cos(t)**2+2*np.sin(t)**2
fd=(F(angle+eps)-F(angle-eps))/(2*eps)
t=np.array([-np.sin(angle),np.cos(angle)]);x0=points[0];egrad=2*A@x0;rgrad=egrad-x0*(x0@egrad)
assert abs(fd-t@rgrad)<1e-8
# The other eigenvector is stationary but is the maximum on the circle.
maximum=np.array([0.,1.]);assert np.linalg.norm(2*(A@maximum-2*maximum))==0
fig,ax=plt.subplots(1,2,figsize=(11,4.8),layout='constrained');theta=np.linspace(0,2*np.pi,500)
ax[0].plot(np.cos(theta),np.sin(theta),c='#93a9b9');ax[0].set_aspect('equal')
P=np.array(points);ax[0].plot(P[:5,0],P[:5,1],'o-',c='#128174',label='採用した円上の点')
for v,c,l in [(-.25*egrad,'#bf4c58','周囲の下降方向'),(-.25*rgrad,'#d47a1f','接下降方向')]:
 ax[0].annotate('',x0+v,x0,arrowprops=dict(arrowstyle='->',color=c,lw=2));ax[0].plot([],[],c=c,label=l)
ax[0].scatter(1,0,marker='*',s=130,c='#22354b',label='最小固有方向')
ax[0].annotate('$x_0$',x0,xytext=(4,8),textcoords='offset points');ax[0].annotate('$x_1$',P[1],xytext=(12,3),textcoords='offset points');ax[0].set_xlim(-.1,1.25);ax[0].set_ylim(-.12,1.15);ax[0].set_xlabel('$x_1$');ax[0].set_ylabel('$x_2$');ax[0].set_title('半径方向を除いてから一歩を作る');ax[0].legend(fontsize=9,loc='lower left')
R=np.array(rows);ax[1].semilogy(R[:16,0],np.maximum(R[:16,3]-1,1e-17),'o-',c='#128174',label='$f(x_k)-1$');ax[1].semilogy(R[:16,0],R[:16,4],'s--',c='#d47a1f',label='$\\|\\mathrm{grad} f(x_k)\\|$');ax[1].set_xlabel('更新回数 $k$');ax[1].set_title('目的の差と接勾配を別々に読む');ax[1].legend();ax[1].grid(alpha=.2)
fig.suptitle('Rayleigh商：$A=\\mathrm{diag}(1,2)$、$\\eta=0.25$',fontsize=16)
for ext in ('svg','png'):fig.savefig(MEDIA/f'riemannian-circle-rayleigh.{ext}',dpi=160)
(ROOT/'verified-numbers.json').write_text(json.dumps({'history':rows,'max_tangent_residual':float(max(orth)),'max_unit_residual':float(max(units)),'directional_finite_difference':float(fd),'directional_gradient':float(t@rgrad),'eigenvalue_oracle':np.linalg.eigvalsh(A).tolist()},indent=2)+'\n')
print(R[:4])
