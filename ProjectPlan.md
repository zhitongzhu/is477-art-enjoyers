# Exploring Artist Representation in Museum Collections

## 1. Overview

Our project will look to investigate how artists from different national and historical backgrounds are being represented in major art museums. We will combine the artwork information with the artists' biographical information in hopes of being able to identify the differences and similarities in the artists represented by the museums collections.

 We will use three publicly available datasets. The Metropolitan Museum of Art Collection API, the Cleveland Museum of Art Open Access API, and Wikidata. We plan on using the museum datasets to provide the information about the artists and their artworks while we use Wikidata to enrich the data and supply any missing or incomplete biographical information about the artists such as their birth dates or maybe their countries of citizenship.

 We will be focused primarily on data acquisition, quality assessment, cleaning, and integration. Our tech stack will include Python and Pandas to retrieve and process the datasets, standardize artist information if needed, identify any duplicate or inconsistent records, and match artists across sources using shared identifiers and verified biographical attributes. We will assess data quality before and after integration, focusing on accuracy, completeness, timeliness, and consistency.

Our last step will be to analyze the integrated dataset to compare artist representation across the two museums. We also plan on creating several data visualizations to illustrate our findings to make the information more non technical. Documentation of our workflow, data sources, and processing decisions will also be made to make sure that our project is transparent and reproducible.


## 2. Team Member Roles and Responsibilities
   Our team has four members who are all responsible for different stages of the curation process. 
Jared — Data Acquisition and Storage
Retrieve artwork and artist data from APIs, collect bio information from wikidata, organize the raw datasets using a consistent file structure, document data sources and acquisition methods, and implement integrity checks.

Bernice - Data Quality Assessment and Cleaning
Evaluate accuracy and completeness of three datasets, identify missing values, duplicate records, inconsistencies, etc, develop scripts to clean and standardize data, document cleaning procedures.

Zhitong - Data Integration and Record Linkage
Develop methods to match artists using Wikidata, handle inconsistent identifiers, implement data integration using Python, Pandas, SQL, create unified dataset

Tongxin - Workflow Automation, Analysis, and Documentation
Develop automated workflow connecting acquisition, quality assessment, cleaning, integration and analysis. Create visualizations. Maintain project docs.

