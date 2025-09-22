# app.R
library(shiny)
library(dplyr)
library(ggplot2)
library(plotly)
library(DT)
library(readr)
library(tidyr)


# ----------------------------
# Load PSL data
# ----------------------------
psl_bb <- read_csv("PSL Complete Dataset (2016-2025).csv", show_col_types = FALSE)

# ----------------------------
# UI
# ----------------------------
ui <- fluidPage(
  titlePanel("PSL Performance Dashboard"),
  
  sidebarLayout(
    sidebarPanel(
      selectInput("season", "Select Season:",
                  choices = sort(unique(psl_bb$season)),
                  selected = max(psl_bb$season)),
      
      selectInput("team", "Select Team:",
                  choices = unique(c(psl_bb$batting_team, psl_bb$bowling_team))),
      
      selectInput("batter", "Select Batter:",
                  choices = unique(psl_bb$batter)),
      
      selectInput("bowler", "Select Bowler:",
                  choices = unique(psl_bb$bowler))
    ),
    
    mainPanel(
      tabsetPanel(
        tabPanel("🏆 Season Overview",
                 plotlyOutput("season_plot1"),
                 plotlyOutput("season_plot2"),
                 plotlyOutput("season_plot3")),
        
        tabPanel("⚡ Team Performance",
                 plotlyOutput("team_plot1"),
                 plotlyOutput("team_plot2"),
                 plotlyOutput("team_plot3")),
        
        tabPanel("🏏 Batter Analysis",
                 plotlyOutput("batter_plot1"),
                 plotlyOutput("batter_plot2"),
                 plotlyOutput("batter_plot3")
        ),
        
        tabPanel("🎯 Bowler Analysis",
                 plotlyOutput("bowler_plot1"),
                 plotlyOutput("bowler_plot2"),
                 plotlyOutput("bowler_plot3")
        )
      )
    )
  )
)

# ----------------------------
# Server
# ----------------------------
server <- function(input, output, session) {
  
  # ========= Season =========
  output$season_plot1 <- renderPlotly({
    df <- psl_bb %>%
      filter(season == input$season) %>%
      group_by(batting_team) %>%
      summarise(runs = sum(batsman_runs + extra_runs, na.rm = TRUE), .groups = "drop")
    
    p <- ggplot(df, aes(x = batting_team, y = runs, fill = batting_team)) +
      geom_col() +
      labs(title = paste("Total Runs by Team -", input$season), x = "", y = "Runs") +
      theme_minimal()
    ggplotly(p)
  })
  
  output$season_plot2 <- renderPlotly({
    df <- psl_bb %>%
      filter(season == input$season, is_wicket == TRUE) %>%
      group_by(bowling_team) %>%
      summarise(wickets = n(), .groups = "drop")
    
    p <- ggplot(df, aes(x = bowling_team, y = wickets, fill = bowling_team)) +
      geom_col() +
      labs(title = paste("Total Wickets by Team -", input$season), x = "", y = "Wickets") +
      theme_minimal()
    ggplotly(p)
  })
  
  output$season_plot3 <- renderPlotly({
    df <- psl_bb %>%
      filter(season == input$season) %>%
      group_by(match_id, over) %>%
      summarise(runs = sum(batsman_runs + extra_runs, na.rm = TRUE), .groups = "drop")
    
    p <- ggplot(df, aes(x = over, y = runs)) +
      geom_line(color = "darkgreen", linewidth = 1.2) +
      labs(title = paste("Runs per Over -", input$season), x = "Over", y = "Runs") +
      theme_minimal()
    ggplotly(p)
  })
  
  # ========= Team =========
  output$team_plot1 <- renderPlotly({
    df <- psl_bb %>%
      filter(batting_team == input$team, season == input$season) %>%
      group_by(extras_type) %>%
      summarise(total = sum(extra_runs, na.rm = TRUE), .groups = "drop") %>%
      filter(!is.na(extras_type))
    
    p <- ggplot(df, aes(x = extras_type, y = total, fill = extras_type)) +
      geom_col() +
      labs(title = paste("Total Extras by Type -", input$team, "-", input$season),
           x = "Extras Type", y = "Runs") +
      theme_minimal()
    ggplotly(p)
  })
  
  output$team_plot2 <- renderPlotly({
    df <- psl_bb %>%
      filter(batting_team == input$team) %>%
      group_by(batter) %>%
      summarise(runs = sum(batsman_runs + extra_runs, na.rm = TRUE), .groups = "drop") %>%
      top_n(10, runs)
    
    p <- ggplot(df, aes(x = reorder(batter, runs), y = runs, fill = batter)) +
      geom_col() +
      coord_flip() +
      labs(title = paste("Top Batters -", input$team), x = "Batter", y = "Runs") +
      theme_minimal()
    ggplotly(p)
  })
  
  output$team_plot3 <- renderPlotly({
    df <- psl_bb %>%
      filter(bowling_team == input$team, is_wicket == TRUE) %>%
      group_by(bowler) %>%
      summarise(wickets = n(), .groups = "drop") %>%
      top_n(10, wickets)
    
    p <- ggplot(df, aes(x = reorder(bowler, wickets), y = wickets, fill = bowler)) +
      geom_col() +
      coord_flip() +
      labs(title = paste("Top Bowlers -", input$team), x = "Bowler", y = "Wickets") +
      theme_minimal()
    ggplotly(p)
  })
  
  # ========= Batter =========
  output$batter_plot1 <- renderPlotly({
    df <- psl_bb %>%
      filter(batter == input$batter) %>%
      group_by(season) %>%
      summarise(runs = sum(batsman_runs + extra_runs, na.rm = TRUE), .groups = "drop")
    
    p <- ggplot(df, aes(x = factor(season), y = runs, group = 1)) +
      geom_line(color = "orange", linewidth = 1.5) +
      geom_point(color = "orange", size = 3) +
      labs(title = paste("Runs by Season -", input$batter), x = "Season", y = "Runs") +
      theme_minimal()
    ggplotly(p)
  })
  
  output$batter_plot2 <- renderPlotly({
    df <- psl_bb %>%
      filter(batter == input$batter) %>%
      group_by(season) %>%
      summarise(
        fours = sum(batsman_runs == 4, na.rm = TRUE),
        sixes = sum(batsman_runs == 6, na.rm = TRUE),
        .groups = "drop"
      ) %>%
      tidyr::pivot_longer(cols = c(fours, sixes), names_to = "boundary_type", values_to = "count")
    
    p <- ggplot(df, aes(x = factor(season), y = count, fill = boundary_type)) +
      geom_col(position = "dodge") +
      labs(
        title = paste("Boundary Distribution by Season -", input$batter),
        x = "Season", y = "Count of Boundaries", fill = "Boundary Type"
      ) +
      theme_minimal()
    
    ggplotly(p)
  })
  
  output$batter_plot3 <- renderPlotly({
    df <- psl_bb %>%
      filter(batter == input$batter) %>%
      group_by(season) %>%
      summarise(
        runs = sum(batsman_runs, na.rm = TRUE),
        balls = n(),
        .groups = "drop"
      ) %>%
      mutate(sr = round(runs / balls * 100, 2))
    
    p <- ggplot(df, aes(x = factor(season), y = sr, group = 1)) +
      geom_line(color = "purple", linewidth = 1.2) +
      geom_point(color = "purple", size = 3) +
      labs(title = paste("Strike Rate by Season -", input$batter),
           x = "Season", y = "Strike Rate") +
      theme_minimal()
    
    ggplotly(p)
  })
  
  # ========= Bowler =========
  output$bowler_plot1 <- renderPlotly({
    df <- psl_bb %>%
      filter(bowler == input$bowler) %>%
      group_by(over) %>%
      summarise(runs = sum(batsman_runs + extra_runs, na.rm = TRUE), balls = n(), .groups = "drop") %>%
      mutate(economy = runs / (balls/6))
    
    p <- ggplot(df, aes(x = over, y = economy)) +
      geom_line(color = "red", linewidth = 1.2) +
      labs(title = paste("Economy by Over -", input$bowler), x = "Over", y = "Economy") +
      theme_minimal()
    ggplotly(p)
  })
  
  output$bowler_plot2 <- renderPlotly({
    df <- psl_bb %>%
      filter(bowler == input$bowler, is_wicket == TRUE) %>%
      group_by(season) %>%
      summarise(wickets = n(), .groups = "drop")
    
    p <- ggplot(df, aes(x = factor(season), y = wickets, group = 1)) +
      geom_line(color = "darkred", linewidth = 1.5) +
      geom_point(color = "darkred", size = 3) +
      labs(title = paste("Wickets by Season -", input$bowler), x = "Season", y = "Wickets") +
      theme_minimal()
    
    ggplotly(p)
  })
  
  output$bowler_plot3 <- renderPlotly({
    df <- psl_bb %>%
      filter(bowler == input$bowler) %>%
      mutate(extra_runs = ifelse(extras_type %in% c("bye", "legbye"), 0, extra_runs)) %>%
      group_by(season) %>%
      summarise(total_runs_conceded = sum(batsman_runs + extra_runs, na.rm = TRUE),
                .groups = "drop")
    
    p <- ggplot(df, aes(x = factor(season), y = total_runs_conceded)) +
      geom_col(fill = "brown") +
      geom_text(aes(label = total_runs_conceded), vjust = -0.5, size = 3) +
      labs(title = paste("Total Runs Conceded by Season -", input$bowler),
           x = "Season", y = "Total Runs Conceded") +
      theme_minimal()
    
    ggplotly(p)
  })
}

# ----------------------------
# Run the App
# ----------------------------
shinyApp(ui, server)