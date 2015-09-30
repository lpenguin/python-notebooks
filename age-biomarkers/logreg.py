# -*- coding: utf-8 -*-
#%%
import pandas as pd
import numpy as np
probe_ds = pd.read_table('data/age-biomarkers/GSE5086.probe.expr', sep=' ')
annotation = pd.read_table('data/age-biomarkers/GPL570.annotation', sep=' ')
#probe_ds.columns = [s.strip('"') for s in probe_ds.columns]
#ds = pd.read_table('data/age-biomarkers/GSE5086.expr', sep=',').set_index('symbol')
#%%
probe_ds = np.log2(probe_ds)
#%%
ds = 2 ** (probe_ds.join(annotation, how='inner')
                  .groupby('symbol')
                  .mean())
#%%
dslog2 = np.log2(ds).applymap(lambda x: x if not np.isinf(x) else np.NaN).dropna()

#%%
import json
characteristics = []
with open('data/age-biomarkers/samples.GSE5086.json') as f:
    for line in f.readlines():
        chars = json.loads(line.rstrip("\n"))
    
        accession = chars['accession']        
        sex = chars['characteristics']['Sex']
        age = float(chars['characteristics']['unnamed_1'].split(":")[1].strip())
        
        characteristics.append(dict(
            accession=accession,
            sex=sex,
            age=age
        ))
characteristics = pd.DataFrame(characteristics).set_index('accession').sort()
characteristics.age.hist()
#%%
median = characteristics.age.median()
threshold = median
#threshold = 20
characteristics['Y'] = characteristics['age'].map(lambda x: 1 if x >= threshold else 0)

#%%

import numpy as np
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression, LinearRegression, Lasso, Ridge
from sklearn import datasets, metrics
from sklearn.preprocessing import StandardScaler
from sklearn.cross_validation import train_test_split, LeaveOneOut,cross_val_score, cross_val_predict
from multiprocessing import Pool
from scipy.stats import pearsonr
import matplotlib
matplotlib.style.use('ggplot')

#%%
males = characteristics[characteristics['sex'] == 'Male'].index.values
females = characteristics[characteristics['sex'] != 'Male'].index.values
ds_male = dslog2[[col for col in dslog2.columns if col in males]]
ds_female = dslog2[[col for col in dslog2.columns if col in females]]
y = dslog2.T.index.map(lambda acc: characteristics.loc[acc]['Y'])
#y = np.random.binomial(1, 0.5, characteristics.shape[0])
X = dslog2.T.as_matrix()
#X = StandardScaler().fit_transform(X)


#%%

def score_model(C):
    model = LogisticRegression(penalty='l1', C=C)
    scores = cross_val_score(model, X, y, cv=5)
    coef = model.fit(X, y).coef_.ravel()
    norm = np.linalg.norm(coef)
    sparsity = np.mean(coef == 0)
    genes_count = np.sum(coef != 0) 
    genes = [(i, c) for i, c in enumerate(coef) if c != 0]
    return (scores.mean(), scores.std(), norm, sparsity, genes_count, genes)
    
scores = pd.DataFrame(dict(C=np.arange(0.001, 2, 0.03 )))

pool = Pool(3)
records = pd.DataFrame.from_records(pool.map(score_model, scores['C'].values))
scores[['score_mean', 'score_std', 'norm', 'sparsity', 'genes_count', 'genes']] = records
#%%
visualize_scores(scores)

#%%
def visualize_scores(scores, score_key='C', threshold=0.85, legend=True):
    gene_lables = dslog2.index
    _t = scores['genes'].map(lambda genes: dict((gene_lables[index], gene) for index, gene in genes)).tolist()
    genes = pd.DataFrame(data=_t, index=scores[score_key])
    
    _threshold = threshold * genes.shape[0]
    genes[genes.index <= 2] \
     .dropna(axis=1, thresh=_threshold) \
     .fillna(0) \
     .plot(legend=legend, figsize=(14, 14))
     
#%%
y = dslog2.T.index.map(lambda acc: characteristics.loc[acc]['age'])
#%%
ages = characteristics.sort()['age'].values

model = LinearRegression().fit(X, y)
gene_lables = dslog2.index
_data = [(gene_lables[index], np.abs(coef)) for index, coef in enumerate(model.coef_)]
coefs_linear = pd.DataFrame.from_records(columns=['gene', 'coef'], data=_data).set_index('gene')
coefs_linear['r'] = coefs_linear.index.map(lambda x: np.abs(pearsonr(dslog2.loc[x].values, ages)[0]))
#%%
coefs_linear.plot(x='coef', y='r', kind='scatter')
#%%
cross_val_score(LinearRegression(), X, y, cv=5)

#%%

def foo():
    X = dslog2.T.as_matrix()
    y = dslog2.T.index.map(lambda acc: characteristics.loc[acc]['age'])
    
    model = Lasso(alpha=1, max_iter=2000)
    def predict_plot(X, y):
        predicted = cross_val_predict(model, X, y, cv=10)
        fig,ax = plt.subplots()
        ax.scatter(y, predicted)
        ax.plot([y.min(), y.max()], [y.min(), y.max()], 'k--', lw=1)
        ax.set_xlabel('Measured')
        ax.set_ylabel('Predicted')
        fig.show()
        
        error_median = np.median(np.abs(y - predicted))
        print("Error median: {}".format(error_median))
        print("Corr: {}".format(
            pearsonr(predicted, y)
        ))
    predict_plot(X, y)
foo()

#%%
X = dslog2.T.as_matrix()
y = dslog2.T.index.map(lambda acc: characteristics.loc[acc]['age'])

def optimize_alpha(alpha):
    model = Lasso(alpha=alpha, normalize=False, max_iter=1000)
    scores = cross_val_score(model, X, y, cv=5)
    coef = model.fit(X, y).coef_.ravel()
    norm = np.linalg.norm(coef)
    sparsity = np.mean(coef == 0)
    genes_count = np.sum(coef != 0) 
    genes = [(i, c) for i, c in enumerate(coef) if c != 0]
    return (scores.mean(), scores.std(), norm, sparsity, genes_count, genes)


def foo():    
    scores_linear = pd.DataFrame(dict(alpha=np.arange(0.001, 1, 0.015 )))

    pool = Pool(3)
    _t = pd.DataFrame.from_records(pool.map(optimize_alpha, (scores_linear.alpha.values)))
    scores_linear[['score_mean', 'score_std', 'norm', 'sparsity', 'genes_count', 'genes']] = _t
    
    return scores_linear
scores_linear = foo()

#%%
visualize_scores(scores_linear, score_key='alpha', threshold=0.0, legend=False)
    
#%%
#[dslog2[col].dropna().plot(kind='kde', legend=False, figsize=(12,12)) for col in dslog2.columns

#%%


model = LinearRegression()

def calc_scores2(in_):
    gene, gene_samples = in_
    model.fit(gene_samples.values[None].T, ages)
    return model.intercept_, model.coef_[0]

revese_scores = list(map(calc_scores2 , dslog2.dropna().iterrows()))
scores2 = pd.DataFrame.from_records(data=revese_scores, columns=['c1', 'c2'], index=dslog2.dropna().index)
scores2.c2.abs().hist()
#%%
genes2 = scores2[scores2.c2.abs() > 35].index

corr2 = pd.DataFrame()
corr2['gene'] = genes2
corr2['r'] = np.abs(corr2.gene.map(lambda x: pearsonr(dslog2.loc[x].values, ages)[0]))
corr2.r.hist()
#calc_scores(ds.iloc[1])
#ds.itertuples()

#%%
# Method 1 correlation
_threshold = 0.1 * genes.shape[0]
high_coef_genes = genes[genes.index <= 0.55] \
 .dropna(axis=1, thresh=_threshold) \
 .columns
 
high_coef_genes


#%%
import scipy
from scipy.stats import pearsonr

#pearsonr(dslog2.loc['AFAP1L1'].values, ages)
corr1 = pd.DataFrame()
#corr1['gene'] = dslog2.dropna().index
corr1['gene'] = high_coef_genes
corr1['r'] = np.abs(corr1.gene.map(lambda x: pearsonr(dslog2.loc[x].values, ages)[0]))
corr1.hist()


