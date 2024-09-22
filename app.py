from flask import Flask, request, render_template, send_file
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from fpdf import FPDF
import tempfile
import os
from mapreduce import process_with_mapreduce  # Placeholder for your MapReduce implementation
from bst import BinarySearchTree  # Implement your BST here

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['dataset']
    if file:
        global cleaned_df, analysis_results, mapreduce_results
        df = pd.read_csv(file)
        cleaned_df = clean_dataset(df)
        analysis_results = analyze_data(cleaned_df)
        mapreduce_results = process_with_mapreduce(cleaned_df)
        store_in_bst(cleaned_df, analysis_results, mapreduce_results)  # Store results in BST
        
        histograms = generate_visualizations(cleaned_df)
        
        return render_template('view_analysis.html', 
                               analysis_results=analysis_results, 
                               mapreduce_results=mapreduce_results,
                               histograms=histograms)
    return "No file uploaded", 400

def clean_dataset(df):
    df = df.dropna()  # Example: Drop rows with missing values
    df = df.select_dtypes(include=['int64', 'float64'])  # Keep only numeric columns
    return df

def analyze_data(df):
    analysis_results = {}
    analysis_results['mean'] = df.mean().to_dict()
    analysis_results['std'] = df.std().to_dict()
    return analysis_results

def create_histogram(df, column):
    buf = BytesIO()
    plt.figure()
    df[column].hist()
    plt.title(f'Histogram of {column}')
    plt.xlabel(column)
    plt.ylabel('Frequency')
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def generate_visualizations(df):
    histograms = {}
    for column in df.columns:
        histograms[column] = create_histogram(df, column)
    return histograms

def store_in_bst(df, analysis_results, mapreduce_results):
    bst = BinarySearchTree()
    bst.insert('cleaned_data', df.to_dict())
    bst.insert('analysis_results', analysis_results)
    bst.insert('mapreduce_results', mapreduce_results)
    return bst

def generate_pdf_report(df, analysis_results, mapreduce_results):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        pdf_file_path = temp_file.name
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add analysis results to PDF
        pdf.cell(200, 10, txt="Analysis Results", ln=True)
        pdf.cell(200, 10, txt="Mean", ln=True)
        for key, value in analysis_results['mean'].items():
            pdf.cell(200, 10, txt=f"  {key}: {value:.2f}", ln=True)
        pdf.cell(200, 10, txt="Standard Deviation", ln=True)
        for key, value in analysis_results['std'].items():
            pdf.cell(200, 10, txt=f"  {key}: {value:.2f}", ln=True)
        
        # Add visualizations to PDF
        temp_image_files = []
        for column in df.columns:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_img_file:
                temp_image_files.append(temp_img_file.name)
                buf = BytesIO()
                plt.figure()
                df[column].hist()
                plt.title(f'Histogram of {column}')
                plt.xlabel(column)
                plt.ylabel('Frequency')
                plt.savefig(buf, format='png')
                buf.seek(0)
                temp_img_file.write(buf.read())
                pdf.add_page()
                pdf.image(temp_img_file.name, x=10, y=pdf.get_y(), w=180)
                pdf.ln(10)
        
        # Add MapReduce outputs to PDF
        pdf.add_page()
        pdf.cell(200, 10, txt="MapReduce Results", ln=True)
        for column, results in mapreduce_results.items():
            pdf.cell(200, 10, txt=f"Results for {column}:", ln=True)
            for key, value in results.items():
                pdf.cell(200, 10, txt=f"  {key}: {value}", ln=True)
        
        # Save PDF
        pdf.output(pdf_file_path)
        
        # Clean up temporary image files
        for file_path in temp_image_files:
            os.remove(file_path)
    
    return pdf_file_path

@app.route('/generate_pdf')
def generate_pdf():
    if 'cleaned_df' not in globals() or 'analysis_results' not in globals() or 'mapreduce_results' not in globals():
        return "No data to generate PDF", 400
    
    report_pdf = generate_pdf_report(cleaned_df, analysis_results, mapreduce_results)
    return send_file(report_pdf, as_attachment=True, download_name="analysis_report.pdf")

if __name__ == '__main__':
    app.run(debug=True)




