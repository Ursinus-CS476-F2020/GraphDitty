import sys
import scipy
import scipy.sparse as sparse
import numpy as np
import numpy.linalg as linalg
import scipy.linalg as sclinalg
from sklearn.cluster import KMeans

def getUnweightedLaplacianEigsDense(W):
    """
    Get eigenvectors of the unweighted Laplacian
    Parameters
    ----------
    W: ndarray(N, N)
        A symmetric similarity matrix that has nonnegative entries everywhere
    
    Returns
    -------
    v: ndarray(N, N)
        A matrix of eigenvectors
    """
    D = scipy.sparse.dia_matrix((W.sum(1).flatten(), 0), W.shape).toarray()
    L = D - W
    _, v = linalg.eigh(L)
    return v

def getSymmetricLaplacianEigsDense(W):
    """
    Get eigenvectors of the weighted symmetric Laplacian
    Parameters
    ----------
    W: ndarray(N, N)
        A symmetric similarity matrix that has nonnegative entries everywhere
    
    Returns
    -------
    v: ndarray(N, N)
        A matrix of eigenvectors
    """
    D = scipy.sparse.dia_matrix((W.sum(1).flatten(), 0), W.shape).toarray()
    L = D - W
    SqrtD = np.sqrt(D)
    SqrtD[SqrtD == 0] = 1.0
    DInvSqrt = 1/SqrtD
    LSym = DInvSqrt.dot(L.dot(DInvSqrt))
    _, v = linalg.eigh(LSym)
    return v

def getRandomWalkLaplacianEigsDense(W):
    """
    Get eigenvectors of the random walk Laplacian by solving
    the generalized eigenvalue problem
    L*u = lam*D*u
    Parameters
    ----------
    W: ndarray(N, N)
        A symmetric similarity matrix that has nonnegative entries everywhere
    
    Returns
    -------
    v: ndarray(N, N)
        A matrix of eigenvectors
    """
    D = scipy.sparse.dia_matrix((W.sum(1).flatten(), 0), W.shape).toarray()
    L = D - W
    _, v = sclinalg.eigh(L, D)
    return v

def spectralClusterSequential(v, dim, time_interval, rownorm=False):
    """
    Given Laplacian eigenvectors associated with a time series, perform 
    spectral clustering, and return a compressed representation of
    the clusters, merging adjacent points with the same label into one cluster
    Parameters
    ----------
    v: ndarray(N, k)
        A matrix of eigenvectors, excluding the zeroeth
    dim: int
        Dimension of spectral clustering, <= k
    time_interval: float
        Length of time in seconds between windows
    rownorm: boolean
        Whether to normalize each row (if using symmetric Laplacian)

    Returns
    -------
    labels: ndarray(N)
        Cluster membership for each point
    intervals_hier: ndarray (N, 2)
        Intervals (in seconds) of annotations
    labels_hier: list(strings)
        Corresponding segment labels for annotations
    """
    assert dim <= v.shape[1]
    x = v[:, 0:dim]
    if rownorm:
        norms = np.sqrt(np.sum(x**2, 1))
        norms[norms == 0] = 1
        x /= norms[:, None]
    labels = KMeans(n_clusters = dim).fit(x).labels_
    splits = np.where(np.abs(labels[1::]-labels[0:-1]) > 0)[0]+1
    splits = np.concatenate(([0], splits, [labels.size]))
    groups = np.split(labels, splits)[1:-1]
    intervals_hier = np.zeros((len(groups), 2))
    intervals_hier[:, 0] = time_interval*splits[0:-1]
    intervals_hier[:, 1] = time_interval*splits[1::]
    labels_hier = ['%i'%g[0] for g in groups]
    return {'labels':labels, 'intervals_hier':intervals_hier, 'labels_hier':labels_hier}