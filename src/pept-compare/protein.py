from Bio import SeqIO
import requests
from io import StringIO
from methods import *
from pyteomics import parser
import numpy as np
from joblib import Memory

memory = Memory(".cache/", verbose=False)

@memory.cache
def download_fasta(protein_id):
    link = f"http://www.uniprot.org/uniprot/{protein_id}.fasta"
    return requests.get(link).text


class Protein:

    def __init__(self, df, accession):
        self.df = df[df['Accession'] == accession]
        self.accession = accession
        self.fasta = self.get_fasta()

    def get_area_sum(self):
        area_columns = [col for col in self.df if col.startswith('Area')]
        area_sum = []
        for a in area_columns:
            df_area = self.df.copy()
            df_area.fillna(0, inplace=True)
            area_sum.append(df_area[a].sum())
        return area_sum

    def get_area_mean(self):
        area_columns = [col for col in self.df if col.startswith('Area')]
        area_mean = []
        for a in area_columns:
            df_area = self.df.copy()
            df_area.fillna(0, inplace=True)
            area_mean.append(df_area[a].mean())
        return area_mean

    def get_spectral_count_sum(self):
        spc_columns = [col for col in self.df if col.startswith('Spectral')]
        spc_sum = []
        for a in spc_columns:
            df_spc = self.df.copy()
            df_spc.fillna(0, inplace=True)
            spc_sum.append(df_spc[a].sum())
        return spc_sum

    def get_spectral_count_mean(self):
        spc_columns = [col for col in self.df if col.startswith('Spectral')]
        spc_mean = []
        for a in spc_columns:
            df_spc = self.df.copy()
            df_spc.fillna(0, inplace=True)
            spc_mean.append(df_spc[a].mean())
        return spc_mean

    def three_peptides(self):
        area_columns = [col for col in self.df if col.startswith('Area')]
        df = self.df.copy()
        df.fillna(0, inplace=True)
        df.sort_values(by=area_columns, ascending=[False, False], inplace=True)
        df = df.head(3)
        df['fold_change'] = df[area_columns[0]] / df[area_columns[1]]
        if df['fold_change'].mean() == np.inf or df['fold_change'].mean() == np.nan:
            return 0
        elif df['fold_change'].mean() < 0:
            return -1/df['fold_change'].mean()
        else:
            return df['fold_change'].mean()

    def get_nbr_of_peptides(self):
        area_columns = [col for col in self.df if col.startswith('Area')]
        nbr_of_peptides = []
        for area in area_columns:
            df_area = self.df.copy()
            df_area.fillna(0, inplace=True)
            nbr_of_peptides.append((df_area[area] != 0).sum())
        return nbr_of_peptides

    def get_id(self):
        return str(self.accession)

    def get_trivial_name(self):
        return str(self.fasta.name.split('|')[2])

    def print(self):
        print(self.df)

    def get_fasta(self):
        data = download_fasta(self.get_id())
        fasta_iterator = SeqIO.parse(StringIO(data), "fasta")
        for fasta in fasta_iterator:
            return fasta

    def get_fasta_seq(self):
        return str(self.fasta.seq)

    def empai(self, base):
        n_observed = self.get_nbr_of_peptides()
        rt = []
        for seq in self.df['Peptide']:
            rt.append(calculate_rt(seq))
        rt_min, rt_max = min(rt), max(rt)

        all_observable_peptides = parser.cleave(self.get_fasta(), 'trypsin', 0)
        observable = []
        for peptide in all_observable_peptides:
            if (calculate_rt(peptide) < rt_max) & (calculate_rt(peptide) > rt_min):
                observable.append(peptide)

        pai = [nbr / len(all_observable_peptides) for nbr in n_observed]

        return (np.power(base, pai)) - 1

