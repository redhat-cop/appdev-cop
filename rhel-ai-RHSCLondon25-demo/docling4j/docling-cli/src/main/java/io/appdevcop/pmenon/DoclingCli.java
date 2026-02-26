package io.appdevcop.pmenon;

import com.ibm.docling.DocumentConverter;

import com.ibm.docling.model.Document;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import picocli.CommandLine;
import picocli.CommandLine.*;

import java.io.File;
import java.nio.file.*;
import java.util.List;
import java.util.concurrent.Callable;

@Command(
        name = "docling-cli",
        mixinStandardHelpOptions = true,
        version = "1.0",
        description = "Convert documents to Markdown and JSON using Docling4j"
)
public class DoclingCli implements Callable<Integer> {

    @Option(
            names = {"-o", "--output"},
            description = "Output directory",
            required = true
    )
    private Path outputDir;

    @Parameters(
            arity = "1..*",
            description = "Input files (PDF, DOCX, HTML, MD, etc.)"
    )
    private List<String> inputFiles;

    @Override
    public Integer call() throws Exception {

        Files.createDirectories(outputDir);

        DocumentConverter converter = new DocumentConverter();

        ObjectMapper mapper = new ObjectMapper();
        mapper.enable(SerializationFeature.INDENT_OUTPUT);

        for (String input : inputFiles) {

            System.out.println("Processing: " + input);
            File file = new File(input);
            var result = converter.convert(file);

            Document document = result.getDocument();

            // ---- Markdown Export ----
            String markdown = document.exportToMarkdown();

            String baseName = new File(input).getName();
            if (baseName.contains(".")) {
                baseName = baseName.substring(0, baseName.lastIndexOf('.'));
            }

            Path mdPath = outputDir.resolve(baseName + ".md");
            Files.writeString(mdPath, markdown);

            // ---- JSON Export ----
            Object jsonObject = document.exportToDict();

            Path jsonPath = outputDir.resolve(baseName + ".json");
            mapper.writeValue(jsonPath.toFile(), jsonObject);

            System.out.println("✓ Saved:");
            System.out.println("  - " + mdPath);
            System.out.println("  - " + jsonPath);
        }

        System.out.println("Conversion complete.");
        return 0;
    }

    public static void main(String[] args) {
        int exitCode = new CommandLine(new DoclingCli()).execute(args);
        System.exit(exitCode);
    }
}