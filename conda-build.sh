#  note. commands below intended to be run line-by-line rather than as a script
#        this is to be used when building locally.
conda build conda.recipe
cp /home/jovyan/miniconda3/envs/mf_base/conda-bld/linux-64/ipyrun-0.4.2*.tar.bz2 /mnt/conda-bld/linux-64
conda convert --platform all /mnt/conda-bld/linux-64/ipyrun-0.4.2*.tar.bz2 --output-dir /mnt/conda-bld
conda index /mnt/conda-bld 