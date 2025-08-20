package com.redhat.rhdg.demo.server.loader;

import org.infinispan.configuration.cache.AbstractStoreConfigurationBuilder;
import org.infinispan.configuration.cache.PersistenceConfigurationBuilder;

public class CustomStoreConfigurationBuilder
		extends AbstractStoreConfigurationBuilder<CustomStoreConfiguration, CustomStoreConfigurationBuilder> {

	public CustomStoreConfigurationBuilder(PersistenceConfigurationBuilder builder) {
		super(builder, CustomStoreConfiguration.attributeDefinitionSet());
	}

	@Override
	public CustomStoreConfiguration create() {
		return new CustomStoreConfiguration(attributes.protect(), async.create());
	}

	@Override
	public CustomStoreConfigurationBuilder self() {
		return this;
	}

}
