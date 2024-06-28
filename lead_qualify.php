<?php
require 'vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;

// FastAPI endpoint URL
$apiUrl = 'http://localhost:8000/qualify';

// Sample lead data
$leadData = [
    [
        "id" => 1,
        "name" => "John Doe",
        "age" => 30,
        "email" => "john@example.com",
        "city" => "New York",
        "state" => "NY",
        "income" => "$150K",
        "linkedin_url" => "https://www.linkedin.com/in/johndoe",
        "instagram_username" => "johndoe",
        "facebook_url" => "https://www.facebook.com/johndoe",
        "twitter_username" => "johndoe"
    ],
    // You can add more lead entries here
];

// Create a new Guzzle client
$client = new Client();

try {
    // Send POST request to the FastAPI endpoint
    $response = $client->post($apiUrl, [
        'json' => $leadData
    ]);

    // Get the response body
    $body = $response->getBody();

    // Parse the JSON response
    $qualifiedLeads = json_decode($body, true);

    // Display the results
    echo "<h1>Qualified Leads</h1>";
    foreach ($qualifiedLeads as $lead) {
        echo "<h2>{$lead['name']}</h2>";
        echo "<p>Score: {$lead['score']}</p>";
        echo "<p>Employment: {$lead['employment']}</p>";
        echo "<pre>{$lead['qualification_summary']}</pre>";
        echo "<hr>";
    }
} catch (RequestException $e) {
    echo "Error: " . $e->getMessage();
}
?>