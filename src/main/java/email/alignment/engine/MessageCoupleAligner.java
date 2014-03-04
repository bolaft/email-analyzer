package email.alignment.engine;

import java.util.Iterator;
import java.util.List;

import org.apache.uima.analysis_engine.AnalysisEngineProcessException;
import org.apache.uima.cas.text.AnnotationIndex;
import org.apache.uima.examples.SourceDocumentInformation;
import org.apache.uima.fit.component.JCasAnnotator_ImplBase;
import org.apache.uima.fit.descriptor.ConfigurationParameter;
import org.apache.uima.jcas.JCas;
import org.apache.uima.jcas.tcas.Annotation;

import common.util.IO;
import common.util.Out;
import email.alignment.model.MessageAlignment;
import fr.univnantes.lina.javautil.IOUtilities;

/**
 * Annotator that aligns lines of MBox messages given as a pair in a JCas
 * TODO check if the last line token (a punctuation) is present 
 * TODO some line are not considered as aligned
 * 
 */
public class MessageCoupleAligner extends JCasAnnotator_ImplBase {

	/** Path dir where to save the tag file */
	public static final String PARAM_TAG_SAVE_PATH = "tagSavePath";
	@ConfigurationParameter(name=PARAM_TAG_SAVE_PATH, mandatory=false)
	private String tagSavePath;

	private static String DEFAULT_SOURCE_DOCUMENT_INFORMATION_ANNOTATION = "org.apache.uima.examples.SourceDocumentInformation";

	@Override
	public void initialize(org.apache.uima.UimaContext context) throws org.apache.uima.resource.ResourceInitializationException {
		Out.print("started", Out.INFO_LEVEL);
		
		super.initialize(context);

		if (tagSavePath != null && !tagSavePath.equalsIgnoreCase("")) {
			Out.print("the following dir content will be deleted: " + tagSavePath, Out.INFO_LEVEL);
			IOUtilities.deleteDirectoryContent(tagSavePath, true);
		}
	};

	@Override
	public void process(JCas aJCas) throws AnalysisEngineProcessException {
		SourceDocumentInformation sourceDocumentInformation = (SourceDocumentInformation) aJCas.getAnnotationIndex(aJCas.getTypeSystem().getType(DEFAULT_SOURCE_DOCUMENT_INFORMATION_ANNOTATION)).iterator().get();

		if (!sourceDocumentInformation.getUri().equals("2013-Feb-18-Mon-20-21-07-CET-paco.f2@wanadoo.fr_2013-Feb-18-Mon-20-37-56-CET-txodom@free.fr")) {
			return;
		} else {
			System.out.println("FOUND SPECIAL ID");
		}

		/** Get the messages */
		AnnotationIndex<Annotation> emailMessageAnnotationIndex = aJCas.getAnnotationIndex(email.types.Message.type);
		Iterator<Annotation> emailMessageAnnotationIterator = emailMessageAnnotationIndex.iterator();
		
		// by the way we remove the empty lines to make easier the alignement process TODO to discuss ?
		String messageSourceText = emailMessageAnnotationIterator.next().getCoveredText().replaceAll("\n\n+", "\n");
		String messageReplyText = emailMessageAnnotationIterator.next().getCoveredText().replaceAll("\n\n+", "\n");

		/** Alignment */
		// return a data structure which will contains the both the source and the reply message lines/sentences aligned
		// if not aligned at a given position but present in one side, will be marked null in the other side 
		MessageAlignment messageAlignement = new MessageAlignment();

		/* ALIGN TWO MESSAGES BASED ON THE WER MEASURE*/
		messageAlignement.alignBasedOnWer(messageSourceText, messageReplyText);
		
		/* ALIGN ARTIFICIALLY TWO MESSAGES ONLY BASED ON THE REPLY MESSAGE AND ITS REPLY LINES */
		//messageAlignement.alignOnlyFromReplyMessage (Arrays.asList(messageReplyText.split("\\n")));
		
		/** tag the aligned */
		List<String> taggedAlignedSourceMessageLines = (List<String>) MessageAlignment.tagSourceMessage(messageAlignement.getAlignedSourceMessageLines(), messageAlignement.getAlignedReplyMessageLines());
				
		for (String line : messageAlignement.getAlignedSourceMessageLines()){
			IO.write(line, "AB_source_lines", true);
		}
		for (String line : taggedAlignedSourceMessageLines){
			IO.write(line, "AB_tagged_lines", true);
		}
		
		/** export the tag*/
		StringBuffer output = new StringBuffer();
		for (int i = 0; i < messageAlignement.getAlignedSourceMessageLines().size() ; i++) {
			// in the alignment procedure we indicate by null the case of non alignment
			String line = (String) messageAlignement.getAlignedReplyMessageLines().get(i);
			//String line = (String) messageAlignement.getAlignedSourceMessageLines().get(i);

			if (line != null) {
				output
					.append(taggedAlignedSourceMessageLines.get(i))
					.append("\t")
					.append((String) messageAlignement.getAlignedSourceMessageLines().get(i))
					.append("\n");
			}
		}
		
		if (tagSavePath != null) {
			output.insert(0, "# "+ tagSavePath+"/"+sourceDocumentInformation.getUri() + "\n");
			IO.write(output.toString(), tagSavePath+"/"+sourceDocumentInformation.getUri(), false);
		}
	}
	
	@Override
	public void collectionProcessComplete() throws AnalysisEngineProcessException {
		super.collectionProcessComplete();
		
		Out.print("done", Out.INFO_LEVEL);
	}
}
