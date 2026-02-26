package org.appdevcop.pamenon.docling;

import ai.docling.serve.api.convert.request.options.OutputFormat;
import ai.docling.serve.api.convert.response.ConvertDocumentResponse;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;

public class App {

    public static void main(String[] args) throws Exception {

        if (args.length < 2) {
            System.out.println("Usage: java -jar app.jar <outputDir> <file1> <file2>...");
            return;
        }

        Path outputDir = Path.of(args[0]);
        Files.createDirectories(outputDir);

        DoclingConverter converter = new DoclingConverter("http://localhost:5001");

        ObjectMapper mapper = new ObjectMapper();

        for (int i = 1; i < args.length; i++) {

            File input = new File(args[i]);
            System.out.println("Processing: " + input.getName());

            // MARKDOWN
            ConvertDocumentResponse mdRes =
                    converter.convert(input, OutputFormat.MARKDOWN);

            String markdown = mdRes.getDocument().getMarkdownContent();
            Path mdPath = outputDir.resolve(input.getName() + ".md");
            Files.writeString(mdPath, markdown);

            // JSON
            ConvertDocumentResponse jsonRes =
                    converter.convert(input, OutputFormat.JSON);

            String json = mapper.writerWithDefaultPrettyPrinter()
                    .writeValueAsString(jsonRes.getDocument());

            Path jsonPath = outputDir.resolve(input.getName() + ".json");
            Files.writeString(jsonPath, json);

            System.out.println("✓ Saved: " + mdPath + " and " + jsonPath);
        }
    }
}