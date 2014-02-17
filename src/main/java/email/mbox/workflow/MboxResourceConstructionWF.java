package email.mbox.workflow;

import static org.apache.uima.fit.factory.AnalysisEngineFactory.createEngineDescription;
import static org.apache.uima.fit.factory.CollectionReaderFactory.createReaderDescription;
import static org.apache.uima.fit.factory.ExternalResourceFactory.createExternalResourceDescription;

import java.io.File;

import org.apache.uima.analysis_engine.AnalysisEngineDescription;
import org.apache.uima.collection.CollectionReaderDescription;
import org.apache.uima.fit.pipeline.SimplePipeline;
import org.apache.uima.resource.ExternalResourceDescription;

import common.util.Out;

import email.mbox.collection.MBoxCollectionReader;
import email.mbox.engine.MBoxResourceBuilder;
import email.mbox.resource.MBoxResource;

public class MboxResourceConstructionWF {

	public static void main(String[] args) throws Exception {
		Out.print("started", Out.INFO_LEVEL);
		
		ExternalResourceDescription mBoxResourceDesc = createExternalResourceDescription(
			MBoxResource.class,
			new File("mbox.bin")
		);
		
		AnalysisEngineDescription aed4 = createEngineDescription(
			MBoxResourceBuilder.class,
			MBoxResourceBuilder.PARAM_MESSAGE_SAVE_DIR, "data/ubuntu-fr/email.message",
			MBoxResourceBuilder.PARAM_RESOURCE_SAVE_FILE, "data/ubuntu-fr/email.digest/email-mbox.res",
			MBoxResourceBuilder.RES_KEY, mBoxResourceDesc
		);

		// je n'ai pas 1263377117.8388.2.camel@amd5000 + des pb d'indentation pourquoi ?
		CollectionReaderDescription crd = createReaderDescription(
			MBoxCollectionReader.class,
			MBoxCollectionReader.PARAM_MBOX_SRCPATH, "data/ubuntu-fr/email.mbox/ubuntu-fr.mbox", 
			MBoxCollectionReader.PARAM_LANGUAGE, "fr",
			MBoxCollectionReader.PARAM_ENCODING, "iso-8859-1"
		);

		SimplePipeline.runPipeline(crd,aed4); //aaed
		
		Out.print("done", Out.INFO_LEVEL);
	}
}
