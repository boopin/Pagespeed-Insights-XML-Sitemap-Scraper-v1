import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

# Set up PageSpeed Insights API
API_KEY = st.secrets["PAGESPEED_API_KEY"]

# Function to fetch URLs from the sitemap and nested sitemaps
def get_sitemap_urls(sitemap_url):
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()  # Raise an error if the request fails
        root = ET.fromstring(response.content)
        urls = []
        # Iterate over sitemap entries
        for elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            loc_url = elem.text
            if loc_url.endswith('.xml'):  # If the URL points to a sitemap, fetch nested URLs
                urls.extend(get_sitemap_urls(loc_url))
            else:
                urls.append(loc_url)
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

        # Extract Lighthouse metrics from the API response
        lighthouse_result = data.get('lighthouseResult', {})
        categories = lighthouse_result.get('categories', {})
        audits = lighthouse_result.get('audits', {})

        # Safely extract category scores
        performance_score = categories.get('performance', {}).get('score', None)
        accessibility_score = categories.get('accessibility', {}).get('score', None)
        best_practices_score = categories.get('best-practices', {}).get('score', None)
        seo_score = categories.get('seo', {}).get('score', None)

        # Handle cases where any of these scores are missing
        performance_score = performance_score * 100 if performance_score is not None else 'N/A'
        accessibility_score = accessibility_score * 100 if accessibility_score is not None else 'N/A'
        best_practices_score = best_practices_score * 100 if best_practices_score is not None else 'N/A'
        seo_score = seo_score * 100 if seo_score is not None else 'N/A'

        # Detailed audit scores for individual metrics
        first_contentful_paint = audits.get('first-contentful-paint', {}).get('displayValue', 'N/A')
        largest_contentful_paint = audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A')
        speed_index = audits.get('speed-index', {}).get('displayValue', 'N/A')
        time_to_interactive = audits.get('interactive', {}).get('displayValue', 'N/A')
        total_blocking_time = audits.get('total-blocking-time', {}).get('displayValue', 'N/A')
        cumulative_layout_shift = audits.get('cumulative-layout-shift', {}).get('displayValue', 'N/A')

        return {
            'URL': url,
            'Performance': performance_score,
            'Accessibility': accessibility_score,
            'Best Practices': best_practices_score,
            'SEO': seo_score,
            'First Contentful Paint': first_contentful_paint,
            'Largest Contentful Paint': largest_contentful_paint,
            'Speed Index': speed_index,
            'Time to Interactive': time_to_interactive,
            'Total Blocking Time': total_blocking_time,
            'Cumulative Layout Shift': cumulative_layout_shift
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching PageSpeed Insights for {url}: {e}")
        return None
    except KeyError:
        st.error(f"KeyError occurred when processing the response for {url}. Some metrics may be missing.")
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

            # Create an empty dataframe for real-time updates
            df_placeholder = st.empty()

            # Create a placeholder for the current URL being processed
            url_status_placeholder = st.empty()

            progress_bar = st.progress(0)
            for i, url in enumerate(urls):
                # Display current progress in terms of URLs being analyzed
                url_status_placeholder.text(f'Analyzing {i+1} out of {len(urls)} URLs: {url}')
                
                result = get_pagespeed_insights(url)
                if result:
                    results.append(result)
                    # Convert results to a dataframe and display them in real-time
                    df = pd.DataFrame(results)
                    df_placeholder.dataframe(df)  # Update the table with new results
                progress_bar.progress((i + 1) / len(urls))  # Update progress bar

            if results:
                st.success('Analysis complete!')
                
                # Allow downloading the final CSV
                csv = pd.DataFrame(results).to_csv(index=False)
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
