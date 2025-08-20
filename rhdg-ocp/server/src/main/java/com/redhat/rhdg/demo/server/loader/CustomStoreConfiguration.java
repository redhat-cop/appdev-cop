package com.redhat.rhdg.demo.server.loader;

import org.infinispan.commons.configuration.BuiltBy;
import org.infinispan.commons.configuration.ConfigurationFor;
import org.infinispan.commons.configuration.attributes.AttributeSet;
import org.infinispan.configuration.cache.AbstractStoreConfiguration;
import org.infinispan.configuration.cache.AsyncStoreConfiguration;
import org.infinispan.configuration.parsing.Element;

@BuiltBy(CustomStoreConfigurationBuilder.class)
@ConfigurationFor(CustomStore.class)
public class CustomStoreConfiguration extends AbstractStoreConfiguration<CustomStoreConfiguration> {

	public static AttributeSet attributeDefinitionSet() {
		return new AttributeSet(CustomStoreConfiguration.class, AbstractStoreConfiguration.attributeDefinitionSet());
	}

	public CustomStoreConfiguration(AttributeSet attributes, AsyncStoreConfiguration async) {
		super(Element.STORE, attributes, async);
	}

}
