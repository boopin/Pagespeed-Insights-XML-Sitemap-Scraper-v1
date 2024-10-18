import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

# Set up PageSpeed Insights API
API_KEY = st.secrets["PAGESPEED_API_KEY"]

# Function to fetch URLs from the sitemap
def get_sitemap_urls(sitemap_url):
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()  # Raise an error if the request fails
        root = ET.fromstring(response.content)
        urls = [elem.text for elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        return urls
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching sitemap: {e}")
        return []
    except ET.ParseError:
        st.error("Error parsing the XML sitemap.")
        return []

# Function to fetch PageSpeed Insights data for a URL
def get_pagespeed_insights(url):
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile&key={API_KEY}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for failed requests
        data = response.json()
        
        lighthouse_result = data.get('lighthouseResult', {})
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
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching PageSpeed Insights for {url}: {e}")
        return None

# Main function to run the app
def main():
    st.title('XML Sitemap PageSpeed Insights Analyzer')
    
    sitemap_url = st.text_input('Enter XML Sitemap URL:')
    
    if st.button('Analyze'):
        if sitemap_url:
            st.info('Fetching URLs from sitemap...')
            urls = get_sitemap_urls(sitemap_url)
            
            if not urls:
                st.error('No URLs found or an error occurred while fetching the sitemap.')
                return
            
            st.info(f'Found {len(urls)} URLs. Analyzing PageSpeed Insights...')
            results = []
            
            progress_bar = st.progress(0)
            for i, url in enumerate(urls):
                result = get_pagespeed_insights(url)
                if result:
                    results.append(result)
                progress_bar.progress((i + 1) / len(urls))
            
            if results:
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
                st.error("No results to display.")
        else:
            st.error('Please enter a valid XML sitemap URL.')

if __name__ == '__main__':
    main()
