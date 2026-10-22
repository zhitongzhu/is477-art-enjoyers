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

## 3. Research/Business Questions
How does the distribution of artists by nationality differ between the Metropolitan Museum of Art and the Cleveland Museum of Art? 

How does the representation of artists from different nationalities vary across historical time periods? 

Which artists appear in both museum collections, and how does the number of artworks associated with these artists differ between the museums?

How complete and consistent is artist information across the museum datasets, and how much can Wikidata improve the availability of biographical information?

## 4. Datasets
Our project will use three publicly accessible datasets to examine artist representation across museum collections. These sources provide complementary information about artworks, artists, and their biographical backgrounds.

__The Metropolitan Museum of Art Collection API__

https://metmuseum.github.io/

The Metropolitan Museum of Art provides an open collection API containing artwork records and associated artist information. Relevant attributes include artwork ID, title, artist name, nationality, birth and death dates, artwork creation dates, and Wikidata identifiers.

We will use this dataset to examine how artists from different backgrounds are represented in the Met's collection. The artist Wikidata identifiers will also help us link museum records to external biographical information.

__The Cleveland Museum of Art Open API__

https://www.clevelandart.org/open-access-api

The Cleveland Museum of Art provides publicly accessible artwork and creator records through its Open Access API. Relevant attributes include artwork ID, title, creator name, creator biography, artwork creation date, department, and classification.

This dataset will allow us to compare artist representation across two museum collections. We plan to identify artists who appear in both collections by comparing artist names and available biographical information.



__Wikidata Query Service__

https://query.wikidata.org/

Wikidata is a collaborative structured knowledge base containing information about people, places, and other entities. We will retrieve artist records containing identifiers, names, dates of birth and death, and citizenship information where available.

Wikidata will serve as an additional reference source to enrich artist records from both museums. It will also support the identification of matching artists and the assessment of missing or inconsistent biographical information.

__Planned Integration__

We plan to integrate the datasets at the artist level. Where available, we will use Wikidata identifiers to link records directly. For records without shared identifiers, we will standardize artist names and compare additional attributes such as birth and death dates to identify possible matches. We will use Python and Pandas to clean and integrate the datasets. We will evaluate the accuracy, completeness, timeliness, and consistency of each dataset before and after integration. We will also document uncertain matches and avoid automatically merging records with insufficient evidence. The resulting dataset will combine museum artwork information with artist biographical attributes, allowing us to compare the representation of artists across both collections.


By answering these questions, we hope to better understand differences in museum collections while demonstrating how data integration and cleaning can improve the quality and usefulness of cultural heritage data.

## 5. Timeline
__10/22:__ All must contribute to making sure the Project Plan is completed and all Team Members are aware of the responsibilities and objectives of our project and should be working on them constantly throughout the project even before the due date.

__11/01:__ Data Acquisition Member will retrieve data from the Museum datasets and connect them to the WikiData and analyze whether or not data is valid to use in answering our research questions

__11/08:__ Data Quality Assessment and Cleaning Member will begin cleaning up datasets, finalizing whether or not the data is helpful to our research questions. Meet after class to discuss findings and discuss if we can continue with the datasets

__11/15:__ Data Integration and Record Linkage should be working on finding ways to connect data between the datasets and be ready to share their analysis, meet to discuss any patterns found in the data that would be significant to our research questions.

__11/19:__ Interim Status Report Due, Workflow and Documentation Member should be ensuring all information and visualizations that are needed are included in the report. All members should contribute their findings and analysis.

__11/30:__ Team Members should meet again after the Status Report to ensure any constraints or gaps that are discussed in the Project Plan have been thoroughly addressed and ensures our report is valid and complete.

__12/1-12/7:__ Team Members will meet to finalize the project and ensure analysis is completed and data is accurate. Workflow and Documentation Member should review the description and visuals before submitting to make sure our work is presented in a way to accurately reflect our analysis.

__12/08:__ Final Project Due.

## 7.Gaps
Data Availability and Integration Feasibility: We still need to examine the actual API responses to determine which attributes are available and how reliably artist records can be linked across the three sources.

Artist Matching Criteria: We need to establish specific rules for matching artists without shared identifiers, including how to handle ambiguous matches and conflicting biographical information.

Data Quality Assessment Methods: We need to determine how to measure accuracy, completeness, timeliness, and consistency before and after integration, including which attributes and metrics to use.

Nationality and Historical Period Definitions: We need to decide how to categorize artists with multiple citizenships or missing nationality information and how to divide artworks into historical time periods for meaningful comparisons.

Workflow and Reproducibility: We need to finalize the structure of our automated workflow, including the order of scripts, data storage formats, and documentation needed to reproduce our results.

