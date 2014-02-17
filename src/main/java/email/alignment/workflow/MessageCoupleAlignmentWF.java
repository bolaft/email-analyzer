package email.alignment.workflow;

import static org.apache.uima.fit.factory.AnalysisEngineFactory.createEngineDescription;
import static org.apache.uima.fit.factory.CollectionReaderFactory.createReaderDescription;
import static org.apache.uima.fit.factory.ExternalResourceFactory.createExternalResourceDescription;

import org.apache.uima.analysis_engine.AnalysisEngineDescription;
import org.apache.uima.collection.CollectionReaderDescription;
import org.apache.uima.fit.pipeline.SimplePipeline;
import org.apache.uima.resource.ExternalResourceDescription;

import common.util.Out;

import email.alignment.collection.MessageCoupleCollectionReader;
import email.alignment.engine.MessageCoupleAligner;
import email.mbox.resource.MBoxResource;

/**
 * Illustrate how to configure 
 * and run annotators with the shared model object.
 */
public class MessageCoupleAlignmentWF {

	public static void main(String[] args) throws Exception {
		Out.print("started", Out.INFO_LEVEL);
		
		// Creation of the external resource description
		ExternalResourceDescription mBoxResourceDesc = createExternalResourceDescription(
			MBoxResource.class,
			"data/ubuntu-fr/email.digest/email-mbox.res"
		);

		// Check the external resource was injected
		AnalysisEngineDescription aed1 = createEngineDescription(
			MessageCoupleAligner.class, 
			MessageCoupleAligner.PARAM_TAG_SAVE_PATH, 
			"data/ubuntu-fr/email.message.tagged"
		);

		CollectionReaderDescription crd = createReaderDescription(
			MessageCoupleCollectionReader.class,
			MessageCoupleCollectionReader.RES_KEY, mBoxResourceDesc,
			MessageCoupleCollectionReader.PARAM_MSG_DIR_PATH,  "data/ubuntu-fr/email.message"
		);
		
		SimplePipeline.runPipeline(crd,aed1); //aaed
		
		Out.print("done", Out.INFO_LEVEL);
	}
}
