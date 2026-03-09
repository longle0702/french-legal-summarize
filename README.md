# French Legal Summarization using CamemBERT

## Dataset
The dataset can be downloaded via:
```bash
wget https://echanges.dila.gouv.fr/OPENDATA/CASS//Freemium_cass_global_20250713-140000.tar.gz
```
## Data Preprocessing
The preprocessing used in this project is partially based on the approach described in the [STRASS method](https://www.aclweb.org/anthology/P19-2034) proposed by Bouscarrat et al. (2019).

## Citation
```bibtex
@inproceedings{bouscarrat-etal-2019-strass,
  title = "{STRASS}: A Light and Effective Method for Extractive Summarization Based on Sentence Embeddings",
  author = "Bouscarrat, Léo and Bonnefoy, Antoine and Peel, Thomas and Pereira, Cécile",
  booktitle = "Proceedings of the 57th Conference of the Association for Computational Linguistics: Student Research Workshop",
  month = jul,
  year = "2019",
  address = "Florence, Italy",
  publisher = "Association for Computational Linguistics",
  url = "https://www.aclweb.org/anthology/P19-2034",
  pages = "243--252"
}

