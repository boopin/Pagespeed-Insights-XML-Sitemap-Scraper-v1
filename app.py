import streamlit as st
import requests
import xml.etree.ElementTree as ET
from googleapiclient.discovery import build
import pandas as pd

# Set up PageSpeed Insights API
API_KEY = st.secrets["PAGESPEED_API_KEY"]

def get_sitemap_urls(sitemap_url):
    response = requests.get(sitemap_url)
    root = ET.fromstring(response.content)
    urls = [elem.text for elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    return urls

def get_pagespeed_insights(url):
    service = build('pagespeedonline', 'v5', developerKey=API_KEY)
    response = service.pagespeedapi().runpagespeed(url=url, strategy='MOBILE').execute()
    
    lighthouse_result = response.get('lighthouseResult', {})
    categories = lighthouse_result.get('categories', {})
    
    performance_score = categories.get('performance', {}).get('score', 0) * 100
    accessibility_score = categories.get('accessibility', {}).get('score', 0) * 100
    best_practices_score = categories.get('best-practices', {}).get('score', 0) * 100
    seo_score = categories.get('seo', {}).get('score', 0) * 100
    
    return {
        'URL': url,
        'Performance': performance_score,
        'Accessibility': accessibility_score,
        'Best Practices': best_practices_score,
        'SEO': seo_score
    }

def main():
    st.title('XML Sitemap PageSpeed Insights Analyzer')
    
    sitemap_url = st.text_input('Enter XML Sitemap URL:')
    
    if st.button('Analyze'):
        if sitemap_url:
            st.info('Fetching URLs from sitemap...')
            urls = get_sitemap_urls(sitemap_url)
            
            st.info(f'Found {len(urls)} URLs. Analyzing PageSpeed Insights...')
            results = []
            
            progress_bar = st.progress(0)
            for i, url in enumerate(urls):
                result = get_pagespeed_insights(url)
                results.append(result)
                progress_bar.progress((i + 1) / len(urls))
            
            df = pd.DataFrame(results)
            st.success('Analysis complete!')
            st.dataframe(df)
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="pagespeed_insights_results.csv",
                mime="text/csv"
            )
        else:
            st.error('Please enter a valid XML sitemap URL.')

if __name__ == '__main__':
    main()
