"""Context schema — defines extractable keys per domain.

Keys are derived from both TSR conditions AND observed gold file context fields.
All values here must be extractable from natural language.
"""
from __future__ import annotations

# domain_id → {key → list of allowed string values, or [] for numeric, or None for bool}
CONTEXT_SCHEMA: dict[str, dict[str, list[str] | None]] = {
    "variant_analysis": {
        "sequencer":          ["illumina", "nanopore", "pacbio"],
        "analysis_type":      ["germline", "somatic", "wgs", "phasing"],
        "phenotype_type":     ["binary", "continuous"],
        "assay":              ["wes", "wgs", "amplicon"],
        "variant_type":       ["SNP", "indel", "structural", "CNV"],
        "genome_build":       ["GRCh37", "GRCh38", "hg19", "hg38"],
        "organism":           ["homo_sapiens", "mus_musculus", "other"],
        "data_format":        ["plink_binary", "vcf", "bcf", "bam"],
        "has_matched_normal": None,   # bool
        "n_samples":          [],     # integer
        "n_cases":            [],
        "n_controls":         [],
        "min_sv_size":        [],
    },
    "transcriptomics": {
        "data_type":           ["short_read", "long_read", "bulk_rna_seq"],
        "assay":               ["scrna_seq", "bulk_rna_seq"],
        "approach":            ["pseudo_alignment", "alignment_based"],
        "organism":            ["homo_sapiens", "mus_musculus", "other"],
        "input_type":          ["gene_list", "ranked_list", "count_matrix", "sorted_bam"],
        "input_format":        ["h5ad", "csv", "tsv", "loom"],
        "annotation":          ["gtf", "gff"],
        "plot_type":           ["heatmap", "volcano", "umap", "tsne", "pca"],
        "paired_end":          None,   # bool
        "has_clusters":        None,
        "has_spliced_unspliced": None,
        "n_samples_per_group": [],    # integer
        "n_cells":             [],
    },
    "epigenomics": {
        "assay":      ["chip_narrow", "chip_broad", "atac_seq", "bisulfite", "cut_and_run"],
        "sequencer":  ["illumina", "nanopore"],
        "paired_end": None,
    },
    "metagenomics": {
        "data_type": ["16S", "shotgun", "metagenome"],
        "approach":  ["kmer", "marker_gene", "assembly"],
        "sequencer": ["illumina", "nanopore", "pacbio"],
    },
    "genome_assembly": {
        "read_type":     ["short_read", "long_read", "hybrid"],
        "kingdom":       ["prokaryote", "eukaryote"],
        "sequencer":     ["illumina", "nanopore", "pacbio", "hifi"],
    },
}

# Human-readable descriptions used in the extraction prompt
CONTEXT_KEY_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "variant_analysis": {
        "sequencer":          "'illumina' (short-read), 'nanopore' or 'pacbio' (long-read)",
        "analysis_type":      "'germline' (inherited variants), 'somatic' (cancer/tumor), 'wgs' (whole genome), 'phasing'",
        "phenotype_type":     "'binary' (case/control GWAS) or 'continuous' (quantitative GWAS)",
        "assay":              "'wes' (whole exome), 'wgs' (whole genome), 'amplicon'",
        "variant_type":       "'SNP', 'indel', 'structural' (SVs), or 'CNV'",
        "genome_build":       "Reference genome: 'GRCh38'/'hg38' or 'GRCh37'/'hg19'",
        "organism":           "'homo_sapiens', 'mus_musculus', or 'other'",
        "data_format":        "Input file format: 'plink_binary', 'vcf', 'bcf', 'bam'",
        "has_matched_normal": "true if a matched normal/control sample is available for somatic calling",
        "n_samples":          "Total number of samples (integer)",
        "n_cases":            "Number of case samples in GWAS (integer)",
        "n_controls":         "Number of control samples in GWAS (integer)",
        "min_sv_size":        "Minimum structural variant size in bp (integer)",
    },
    "transcriptomics": {
        "data_type":           "'short_read' (Illumina), 'long_read' (PacBio/Nanopore), or 'bulk_rna_seq'",
        "assay":               "'scrna_seq' for single-cell, 'bulk_rna_seq' for bulk",
        "approach":            "'pseudo_alignment' (kallisto/salmon) or 'alignment_based' (STAR/HISAT2)",
        "organism":            "'homo_sapiens', 'mus_musculus', or 'other'",
        "input_type":          "'gene_list' (ORA enrichment), 'ranked_list' (GSEA), 'count_matrix', 'sorted_bam'",
        "input_format":        "File format: 'h5ad', 'csv', 'tsv', 'loom'",
        "annotation":          "Genome annotation file: 'gtf' or 'gff'",
        "plot_type":           "Visualization type: 'heatmap', 'volcano', 'umap', 'tsne', 'pca'",
        "paired_end":          "true if reads are paired-end, false if single-end",
        "has_clusters":        "true if cell clusters are already assigned before this step",
        "has_spliced_unspliced": "true if both spliced and unspliced count matrices are available (for RNA velocity)",
        "n_samples_per_group": "Number of biological replicates per condition (integer)",
        "n_cells":             "Number of cells in the dataset (integer)",
    },
    "epigenomics": {
        "assay":      "'chip_narrow' (TF/H3K27ac), 'chip_broad' (H3K27me3), 'atac_seq', 'bisulfite', 'cut_and_run'",
        "sequencer":  "'illumina' or 'nanopore'",
        "paired_end": "true if reads are paired-end",
    },
    "metagenomics": {
        "data_type": "'16S' (amplicon), 'shotgun' (WGS metagenomics), 'metagenome'",
        "approach":  "'kmer', 'marker_gene', or 'assembly'",
        "sequencer": "'illumina', 'nanopore', or 'pacbio'",
    },
    "genome_assembly": {
        "read_type": "'short_read', 'long_read', or 'hybrid'",
        "kingdom":   "'prokaryote' or 'eukaryote'",
        "sequencer": "'illumina', 'nanopore', 'pacbio', or 'hifi'",
    },
}


def get_schema(domain_id: str) -> dict[str, list[str]]:
    return CONTEXT_SCHEMA.get(domain_id, {})


def get_descriptions(domain_id: str) -> dict[str, str]:
    return CONTEXT_KEY_DESCRIPTIONS.get(domain_id, {})


def format_schema_hint(domain_id: str) -> str:
    schema = get_schema(domain_id)
    descriptions = get_descriptions(domain_id)
    if not schema:
        return "(no structured context keys defined for this domain)"

    lines = []
    for key, allowed in schema.items():
        desc = descriptions.get(key, "")
        if allowed:
            lines.append(f'  "{key}": one of {allowed}  — {desc}')
        else:
            lines.append(f'  "{key}": integer  — {desc}')
    return "\n".join(lines)
