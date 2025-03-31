import logging
from langchain.schema import Document
from utils.general_utils import *
from utils.content_construction import *
logger = logging.getLogger(__name__)

def parse_to_document_objects(metadata):
    logger.info("Converting metadata to Document objects")
    documents = []
    programs_en = {}
    programs_fr = {}
    program_info_en = {}
    program_info_fr = {}
    for snippet in metadata:
        try:
            english_data = snippet.get('English', {})
            french_data = snippet.get('French', {})
            course = snippet['course']
            if course not in programs_en:
                programs_en[course] = 1
                programs_en['modified'] = snippet.get('modified')
            else:
                programs_en[course] += 1
                programs_en['modified'] = min(programs_en['modified'], snippet.get('modified'))
            if course not in programs_fr:
                programs_fr[course] = 1
                programs_fr['modified'] = snippet.get('modified')
            else:
                programs_fr[course] += 1
                programs_fr['modified'] = min(programs_fr['modified'], snippet.get('modified'))
            program_name = format_course_name(snippet['course'])
            if program_name not in program_info_en:
                program_info_en[program_name] = {}
            if program_name not in program_info_fr:
                program_info_fr[program_name] = {}
            program_info_en[program_name][english_data['title']] = create_english_program_info(english_data, last_modified=snippet.get('modified'))
            program_info_fr[program_name][french_data['title']] = create_french_program_info(french_data, last_modified=snippet.get('modified'))
            en_pdf_con = english_data.get("pdf_content")
            if en_pdf_con != "" and en_pdf_con != None:
                english_doc = Document(
                    page_content=construct_content_for_embedding_en(english_data, course=snippet['course']),
                    metadata = sanitize_metadata({k: replace_null(v) for k, v in english_data.items() if k != 'pdf_content'}, language='en'),
            )
            else:
                logger.warning(f"Skipping English document for {english_data.get("title")} due to missing PDF content")
                english_doc = None

            fr_pdf_con = french_data.get("pdf_content")
            if fr_pdf_con != "" and fr_pdf_con != None:
                french_doc = Document(
                    page_content=construct_content_for_embedding_fr(french_data, course=snippet['course']),
                    metadata = sanitize_metadata({k: replace_null(v) for k, v in french_data.items() if k != 'pdf_content'}, language='fr'),
                )
            else:
                logger.warning(f"Skipping French document for {french_data.get("title")} due to missing PDF content")
                french_doc = None
            
            if french_doc != None:
                french_doc.metadata['last_modified'] = snippet.get('modified')
                documents.extend([french_doc])
                logger.info(f"Converted snippet {french_data.get("title")} to Document object")
            
            if english_doc != None:
                english_doc.metadata['last_modified'] = snippet.get('modified')
                documents.extend([english_doc])
                logger.info(f"Converted snippet {english_data.get("title")} to Document object")
        except Exception as e:
            logger.error(f"Document conversion failed: {str(e)}", exc_info=True)
            continue
    specific_program_en = create_content_for_specific_course(program_info_en, language='en')
    specific_program_fr = create_content_for_specific_course(program_info_fr, language='fr')
    overall_en = create_overall_snippet_courses_en(programs_en)
    overall_fr = create_overall_snippet_courses_fr(programs_fr)
    documents.extend(specific_program_en)
    documents.extend(specific_program_fr)
    documents.extend([overall_en])
    documents.extend([overall_fr])
    return documents