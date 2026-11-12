from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results';P=ROOT/'figures';P.mkdir(exist_ok=True)
styles={'adaptive_empirical':('R9 adaptive empirical','-o'),'random_informative':('Fair random','--s'),'greedy_expected_cert':('One-step expected certificate','-.^'),'dopt':('D-optimal','-.*')}
for kind,label,upper in [('yeast','Yeast GPCA/MAPPIT external study (retrospective)',9),('human','Human within-study assay 1 (retrospective)',11)]:
    s=pd.read_csv(R/f'{kind}_all100_summary.csv')
    fig,ax=plt.subplots(figsize=(8.2,4.3),dpi=140)
    for name,(title,fmt) in styles.items():
        z=s[s.method==name].sort_values('budget')
        ax.plot(z.budget,z.expected_certified_actions,fmt,label=title,linewidth=1.9,markersize=6)
    ax.axhline(upper,linestyle=':',linewidth=1.2,color='gray',label=f'Full-information ceiling: {upper}')
    ax.set_xlabel('Maximum revealed informative labels per panel',fontsize=10)
    ax.set_ylabel('Mean certified strict action winners (panels)',fontsize=10)
    ax.set_title(label,fontsize=11)
    ax.set_xlim(4.5,20.5);ax.set_xticks([5,8,10,15,20]);ax.set_ylim(0,upper+1)
    ax.grid(axis='y',alpha=.2)
    ax.legend(loc='lower right',fontsize=7.8,ncol=2,frameon=False)
    fig.tight_layout();fig.savefig(P/f'{kind}_budget_curves.pdf',bbox_inches='tight');fig.savefig(P/f'{kind}_budget_curves.png',bbox_inches='tight');plt.close(fig)

# Effect concentration and source scope, never pool distinct sources as independent replicates.
fig,ax=plt.subplots(figsize=(7.6,3.6),dpi=150)
labels=['R9 human assay2/3\n71 panels','R10 yeast GPCA/MAPPIT\n74 panels','R10 human assay1\n44 panels']
vals=[1.73,.69,.26];n=[71,74,44]
ax.bar(range(3),[v/den for v,den in zip(vals,n)],color=['#738c9c','#66988c','#b3a0a2'])
ax.set_xticks(range(3));ax.set_xticklabels(labels,fontsize=9)
ax.set_ylabel('Additional certified panels per evaluated panel')
ax.set_title('Observed advantage over fair random at cap=10\n(different sources, NOT pooled)',fontsize=10)
ax.grid(axis='y',alpha=.2)
for i,(val,den) in enumerate(zip(vals,n)):
 ax.text(i,val/den+.0008,f'+{val:.2f} / {den}',ha='center',fontsize=9)
ax.set_ylim(0,.03);fig.tight_layout();fig.savefig(P/'increment_scope.pdf',bbox_inches='tight');fig.savefig(P/'increment_scope.png',bbox_inches='tight');plt.close(fig)
print('plots done')
