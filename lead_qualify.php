<?php
require 'vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;

// FastAPI endpoint URL
$apiUrl = 'https://lead-qualifier-67eh.onrender.com/qualify';

// Sample lead data
$leadData = [
    [
        "id" => 1,
        "name" => "Scott Soderstrom",
        "age" => 58,
        "email" => "ssoderstrom@gmail.com",
        "city" => "Seattle",
        "state" => "WA",
        "income" => "$85K",
        "linkedin_url" => "https://www.linkedin.com/in/soderalohastrom/",
        "instagram_username" => "soderalohastrom",
        "facebook_url" => "https://www.facebook.com/scott.soderstrom/",
        "twitter_username" => "soderalohastom"
    ],
    // You can add more lead entries here
];

// Create a new Guzzle client
$client = new Client();

try {
    $response = $client->post($apiUrl, [
        'json' => $leadData
    ]);

    $body = $response->getBody();
    $qualifiedLeads = json_decode($body, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception("Failed to parse JSON response: " . json_last_error_msg());
    }

    if (!is_array($qualifiedLeads)) {
        throw new Exception("Unexpected response format");
    }

    echo "<h1>Qualified Leads</h1>";
    foreach ($qualifiedLeads as $lead) {
        echo "<h2>" . htmlspecialchars($lead['name']) . "</h2>";
        echo "<p>Score: " . htmlspecialchars($lead['score']) . "</p>";
        echo "<p>Employment: " . htmlspecialchars($lead['employment']) . "</p>";
        echo "<pre>" . htmlspecialchars($lead['qualification_summary']) . "</pre>";
        echo "<hr>";
    }
} catch (RequestException $e) {
    echo "HTTP Request Error: " . htmlspecialchars($e->getMessage());
} catch (Exception $e) {
    echo "Error: " . htmlspecialchars($e->getMessage());
}
?>