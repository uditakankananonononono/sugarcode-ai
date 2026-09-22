from __future__ import annotations
import math
import numpy as np
from scipy import ndimage


def _segment(img: np.ndarray, threshold_pct: float = 60.0) -> tuple[np.ndarray, int]:
    """Background-normalized threshold segmentation + watershed-free labeling."""
    bg = ndimage.gaussian_filter(img.astype(float), sigma=max(img.shape) / 8)
    corrected = img.astype(float) - bg
    corrected -= corrected.min()
    if corrected.max() > 0:
        corrected /= corrected.max()
    mask = corrected > (threshold_pct / 100.0 * corrected.max())
    mask = ndimage.binary_opening(mask, iterations=1)
    mask = ndimage.binary_fill_holes(mask)
    labels, n = ndimage.label(mask)
    return labels, n


def count_cells(image: list[list[float]], threshold_pct: float = 60.0) -> dict:
    """Count cells in a grayscale microscopy image (2D array)."""
    img = np.asarray(image, dtype=float)
    if img.ndim != 2:
        raise ValueError("expecting a 2D grayscale image")
    labels, n = _segment(img, threshold_pct)
    sizes = ndimage.sum(np.ones_like(labels), labels, range(1, n + 1))
    sizes = np.array(sizes) if n else np.array([])
    # split filter: drop debris (<5 px) 
    real = int((sizes >= 5).sum()) if n else 0
    return {
        "raw_objects": n,
        "cell_count": real,
        "debris_filtered": n - real,
        "mean_cell_area_px": round(float(sizes[sizes >= 5].mean()), 1) if real else 0.0,
        "coverage_fraction": round(float((labels > 0).mean()), 4),
    }


def analyze_image(image: list[list[float]], threshold_pct: float = 60.0) -> dict:
    """Full analysis: count, morphology per cell, culture-health summary."""
    img = np.asarray(image, dtype=float)
    labels, n = _segment(img, threshold_pct)
    cells = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(labels == i)
        if len(ys) < 5:
            continue
        area = len(ys)
        h = ys.max() - ys.min() + 1
        w = xs.max() - xs.min() + 1
        aspect = max(h, w) / max(1, min(h, w))
        perimeter = float(np.sum(ndimage.binary_erosion(labels == i) ^ (labels == i)))
        circularity = round(4 * np.pi * area / max(perimeter ** 2, 1e-9), 3)
        intensity = float(img[ys, xs].mean())
        cells.append({"id": i, "area_px": area, "aspect_ratio": round(aspect, 2),
                      "circularity": circularity, "mean_intensity": round(intensity, 2),
                      "centroid": [float(ys.mean()), float(xs.mean())]})
    health = _culture_health(cells, img)
    return {
        "cell_count": len(cells),
        "cells": cells,
        "culture_health": health,
        "segmentation_qc": {"objects_raw": n, "objects_kept": len(cells),
                            "correction": "size-filter + fill-holes + opening"},
    }


def _culture_health(cells: list[dict], img: np.ndarray) -> dict:
    if not cells:
        return {"confluence_pct": 0.0, "morphology": "no cells detected", "verdict": "empty/failed"}
    area = sum(c["area_px"] for c in cells)
    confluence = round(100 * area / img.size, 1)
    round_cells = sum(1 for c in cells if c["circularity"] > 0.8 and c["area_px"] < 50)
    frac_round = round_cells / len(cells)
    morphology = ("healthy spread" if frac_round < 0.15 else
                  "stress - many rounded cells" if frac_round < 0.4 else
                  "poor - predominantly rounded/detaching")
    return {"confluence_pct": confluence, "rounded_fraction": round(frac_round, 3),
            "morphology": morphology,
            "verdict": "passage soon" if confluence > 80 else "healthy" if frac_round < 0.15 else "check conditions"}

# --- robust microscopy segmentation and phenotypic-screen analytics ----------
def validate_image(image, *, pixel_size_um: float=1.0) -> np.ndarray:
    """Validate a 2-D microscopy frame and normalize it to finite float data."""
    img=np.asarray(image,float)
    if img.ndim!=2 or min(img.shape)<8: raise ValueError("image must be a 2-D array with each dimension >= 8")
    if not np.all(np.isfinite(img)): raise ValueError("image contains non-finite pixels")
    if pixel_size_um<=0: raise ValueError("pixel_size_um must be positive")
    if np.ptp(img)==0: raise ValueError("image has no intensity contrast")
    return img


def corrected_segmentation(image, *, pixel_size_um: float=1, min_area_um2: float=10,
                           threshold_method: str="otsu") -> dict:
    """Segment cells with flat-field correction, Otsu thresholding, and overlap splitting."""
    img=validate_image(image,pixel_size_um=pixel_size_um)
    if min_area_um2<=0: raise ValueError("min_area_um2 must be positive")
    if threshold_method not in {"otsu","adaptive"}: raise ValueError("threshold_method must be otsu or adaptive")
    smooth=ndimage.gaussian_filter(img,1); bg=ndimage.gaussian_filter(img,max(img.shape)/8); corrected=smooth-bg; corrected-=corrected.min(); corrected/=max(corrected.max(),1e-12)
    if threshold_method=="otsu":
        hist,bins=np.histogram(corrected,256,(0,1)); prob=hist/hist.sum(); omega=np.cumsum(prob); mu=np.cumsum(prob*np.arange(256)); total=mu[-1]; between=(total*omega-mu)**2/np.maximum(omega*(1-omega),1e-15); threshold=float(np.argmax(between)/255)
        mask=corrected>threshold
    else:
        local=ndimage.gaussian_filter(corrected,max(2,min(img.shape)/16)); threshold=float(np.mean(local)); mask=corrected>local
    mask=ndimage.binary_fill_holes(ndimage.binary_opening(mask)); distance=ndimage.distance_transform_edt(mask); maxima=(distance==ndimage.maximum_filter(distance,size=5))&(distance>1)
    markers,nmark=ndimage.label(maxima)
    # Voronoi assignment within foreground splits touching objects without skimage.
    if nmark:
        _,inds=ndimage.distance_transform_edt(~maxima,return_indices=True); labels=markers[tuple(inds)]; labels*=mask
    else: labels,_=ndimage.label(mask)
    n=int(labels.max()); min_px=max(1,min_area_um2/pixel_size_um**2); keep=[]
    for j in range(1,n+1):
        if np.sum(labels==j)>=min_px: keep.append(j)
    clean=np.zeros_like(labels); 
    for new,old in enumerate(keep,1): clean[labels==old]=new
    return {"labels":clean.tolist(),"cell_count":len(keep),"threshold":threshold,"threshold_method":threshold_method,"pixel_size_um":pixel_size_um,"minimum_area_um2":min_area_um2,"objects_before_correction":n,"objects_removed":n-len(keep),"model_status":"mechanistic hermetic image processing; no trained model claim"}


def morphology_table(image, segmentation: dict) -> list[dict]:
    """Extract actionable per-cell morphology and intensity measurements."""
    img=validate_image(image,pixel_size_um=segmentation["pixel_size_um"]); labels=np.asarray(segmentation["labels"],int); px=segmentation["pixel_size_um"]; rows=[]
    if labels.shape!=img.shape: raise ValueError("segmentation labels must match image shape")
    for j in range(1,int(labels.max())+1):
        mask=labels==j; ys,xs=np.nonzero(mask); area=len(xs); eroded=ndimage.binary_erosion(mask); perimeter=np.sum(mask^eroded)*px; cy,cx=ys.mean(),xs.mean(); cov=np.cov(np.column_stack([ys,xs]).T) if area>1 else np.eye(2); eig=np.linalg.eigvalsh(cov); aspect=math.sqrt(max(eig[-1],1e-12)/max(eig[0],1e-12))
        rows.append({"cell_id":j,"area_um2":area*px**2,"perimeter_um":float(perimeter),"circularity":float(4*np.pi*area*px**2/max(perimeter**2,1e-12)),"aspect_ratio":float(aspect),"mean_intensity":float(img[mask].mean()),"integrated_intensity":float(img[mask].sum()),"centroid_y_px":float(cy),"centroid_x_px":float(cx),"edge_touching":bool(np.any(ys==0)|np.any(xs==0)|np.any(ys==img.shape[0]-1)|np.any(xs==img.shape[1]-1))})
    return rows


def enhancement_features(image, segmentation: dict, cells: list[dict]) -> dict:
    """Compute 50 image- and cell-derived screening diagnostics."""
    img=np.asarray(image,float); lab=np.asarray(segmentation["labels"]); area=np.array([x["area_um2"] for x in cells]); per=np.array([x["perimeter_um"] for x in cells]); circ=np.array([x["circularity"] for x in cells]); asp=np.array([x["aspect_ratio"] for x in cells]); inten=np.array([x["mean_intensity"] for x in cells]); integ=np.array([x["integrated_intensity"] for x in cells]); yy=np.array([x["centroid_y_px"] for x in cells]); xx=np.array([x["centroid_x_px"] for x in cells])
    if not cells: raise ValueError("no cells available for diagnostics")
    out={"cell_count":len(cells),"objects_before_correction":segmentation["objects_before_correction"],"objects_removed":segmentation["objects_removed"],"retention_fraction":len(cells)/max(segmentation["objects_before_correction"],1),"threshold":segmentation["threshold"],"foreground_fraction":float(np.mean(lab>0)),"image_mean_intensity":float(img.mean()),"image_intensity_range":float(np.ptp(img)),"background_mean_intensity":float(img[lab==0].mean()) if np.any(lab==0) else 0.,"foreground_mean_intensity":float(img[lab>0].mean()),"foreground_background_ratio":float(img[lab>0].mean()/max(img[lab==0].mean(),1e-12)) if np.any(lab==0) else 0.,"area_min_um2":float(area.min()),"area_max_um2":float(area.max()),"area_mean_um2":float(area.mean()),"area_median_um2":float(np.median(area)),"area_cv":float(area.std()/area.mean()),"perimeter_min_um":float(per.min()),"perimeter_max_um":float(per.max()),"perimeter_mean_um":float(per.mean()),"circularity_min":float(circ.min()),"circularity_max":float(circ.max()),"circularity_mean":float(circ.mean()),"circularity_median":float(np.median(circ)),"round_cell_count":int(np.sum(circ>.8)),"irregular_cell_count":int(np.sum(circ<.5)),"aspect_ratio_min":float(asp.min()),"aspect_ratio_max":float(asp.max()),"aspect_ratio_mean":float(asp.mean()),"elongated_cell_count":int(np.sum(asp>2)),"mean_intensity_min":float(inten.min()),"mean_intensity_max":float(inten.max()),"mean_intensity_mean":float(inten.mean()),"mean_intensity_cv":float(inten.std()/max(inten.mean(),1e-12)),"integrated_intensity_min":float(integ.min()),"integrated_intensity_max":float(integ.max()),"integrated_intensity_total":float(integ.sum()),"centroid_x_min":float(xx.min()),"centroid_x_max":float(xx.max()),"centroid_y_min":float(yy.min()),"centroid_y_max":float(yy.max()),"centroid_x_span":float(np.ptp(xx)),"centroid_y_span":float(np.ptp(yy)),"edge_touching_count":sum(x["edge_touching"] for x in cells),"non_edge_cell_count":sum(not x["edge_touching"] for x in cells),"nearest_centroid_distance_mean":float(np.mean([min(math.hypot(x-a,y-b) for a,b in zip(xx,yy) if (a,b)!=(x,y)) for x,y in zip(xx,yy)])) if len(cells)>1 else 0.,"cell_density_per_1kpx":len(cells)/img.size*1000,"coverage_area_um2":float(np.sum(lab>0)*segmentation["pixel_size_um"]**2),"culture_confluence_pct":float(np.mean(lab>0)*100),"intensity_area_correlation":float(np.corrcoef(area,inten)[0,1]) if len(cells)>1 and area.std()>0 and inten.std()>0 else 0.,"morphology_health_score":float(np.clip((np.mean(circ)+1/np.mean(asp))/2,0,1))}
    assert len(out)==50
    return out


def analyze_microscopy(image, *, pixel_size_um: float=1, min_area_um2: float=10, threshold_method="otsu") -> dict:
    """Return a phenotypic-screen-ready segmentation and quantitative QC report."""
    seg=corrected_segmentation(image,pixel_size_um=pixel_size_um,min_area_um2=min_area_um2,threshold_method=threshold_method); cells=morphology_table(image,seg); diag=enhancement_features(image,seg,cells)
    return {"segmentation":seg,"cells":cells,"diagnostics":diag,"diagnostic_count":50,"culture_health":{"confluence_pct":diag["culture_confluence_pct"],"health_score":diag["morphology_health_score"],"decision":"review" if diag["morphology_health_score"]<.5 else "acceptable"},"recommended_actions":["inspect overlay for split/merge errors","review edge-touching objects","compare phenotype against plate controls"]}
