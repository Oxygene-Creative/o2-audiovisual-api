from app.models.agents import QuotedAnswer
from langchain_elasticsearch import ElasticsearchStore
from app.analyzers.embeddings import embedding_model
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.llm import llm
import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_es_retriever(indexes):
    vector_store = ElasticsearchStore(
        es_url=os.environ['ELASTIC_CLOUD_URL'],
        es_api_key=os.environ['ELASTIC_API_KEY'],
        index_name=indexes,
        embedding=embeddings,
    )
    
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold", search_kwargs={"score_threshold": 0.2}
    )
    
    return retriever

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def create_rag_chain():
    prompt = ChatPromptTemplate.from_template(
        """Answer the question based only on the context provided.
        Make sure you give citations
        (majorly use id of the document and the relevant quote).

        format for link that views the citation doc (http://localhost:3000/administration/asset-viewer?source=[print or tv or radio etc]&id=1234)
    Context: {context}
    Question: {question}"""
    )
   
    vector_retriever = get_es_retriever("radio_*")
   
    chain = (
        {"context": vector_retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

def invoke_rag_chain(question: str):
    chain = create_rag_chain()
    
    response = chain.invoke(question)
    
    return response