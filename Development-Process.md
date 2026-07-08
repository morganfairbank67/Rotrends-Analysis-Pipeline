### Goal:
An automated data and machine learning pipeline to identify market gaps within Roblox.
### Achieve this through:
- Continously scraping data from rotrends by monitering high-performing games
- Validating the extracted data with Pydantic
- Store data into a PostgreSQL database (Supabase)
- Using game descriptions to generate embeddings through Sentence-Transformers
    - Clustering(K-Means): grouping games into mechanical sub-genres
    - Scoring: Calculating an opportunity score (Total CCU / Number of Competing games)
- Presenting said data on dashboard using Streamlit to visualise historical trends and market saturation on interactive charts
- Notifications on summaries: Using something like a discord webhook to automatically push summaries to a private server


### Approach Diary
- Intially looking into playwright as I have seen that it's especially good for sites like Rotrend that stop or makes botting/scrapping difficult.
- Already had some experience in HTML so understood scrapping data at a basic level but after watching some videos, have a better understanding in being able to locate specific classes and taking the data from inside of it
- Since Rotrend had a login page I needed to find a way for playwright to login before proceeding to the actual pages I needed to scrape from. This is where I learned about the playwright's function codegen which allowed me to record the actions I made on screen which allowed me to figure out a function to be able to log in. This required a lot or trial and error as the direct code from codegen actually had a lot of issues due to Rotrend having functions to stop botting. So, I learned that the username needed to be typed out sequentially as the Playwright function .fill() caused an input that would vanish after clicking off the box so I used the press_sequentially() function to simulate real human typing. After, fixing that issue I then discovered that if it began typing the moment the box was clicked it the first input into the box would be erased so adding a sleep between clicking and typing fixed this. The password seemed like there were less restrictions allowing a straight paste in.
- After using inspect to find the row class and cell class, I was able to scrape data for game name and 4 other metrics. This is where I came to the dilemma where I needed as much data from each game as possible. So, excluding the paid metrics there were 26 free metrics. I needed to find a way to be able to select all the preferences I need. At the start, I used codegen intially but saw its shortcomings as sometimes the preferences did not entirely save from one page to the other and if I used the code/function more than once then I would run into an error. So, instead I had a good look into the HTML to see what I could find, looking through the attributes I noticed that title within the metrics drop down table was something I could use to get each button and then also seen that there was a unique class attached that shows if the metric was selected or not. So, this made sure that I was only clicking  metrics that were not already selected.
- The main function of the extract.py file was to take data from Rotrend, intially I made a variable for each child within the row but found this ineffective as I wanted Game name, date extracted, category and the 26 metrics. Instead, I get each game row and look at every cell within the row and match it with the header. This ensures data scrapped comes from the cell under the right header.