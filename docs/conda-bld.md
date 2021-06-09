# conda-bld

__note__. bash commands are assumed to be called from the root of this repo.

## mount conda channel

- mount the network location

```bash
mkdir /mnt/conda-bld
sudo mount -t drvfs '\\barbados\apps\conda\conda-bld' /mnt/conda-bld
```

## conda build

```bash
wsl
conda activate base_mf
# add conda mf conda channel if not already there... check with command below...
# conda config --show
conda config --add channels file:///mnt/conda-bld #  as this depends on other internal packages
conda build conda.recipe
```

- note. builds here: `\\wsl$\Ubuntu-20.04\home\gunstonej\miniconda3\envs\base_mf\conda-bld` unless `--croot /mnt/c/engDev/channel` is specified
- once built check its working, then publish to MF network

## publish to MF

- copy and paste the linux-64 files `*.tar.bz2` into `\\barbados\apps\conda\conda-bld\linux-64`
- and convert to all platforms

```bash
conda convert --platform all /mnt/conda-bld/linux-64/ipyrun*.tar.bz2
conda index /mnt/conda-bld
```

- install from network channel

```bash
conda config --add channels file:///mnt/conda-bld
conda install ipyrun
# or 
conda install -c file:///mnt/conda-bld ipyrun
```
