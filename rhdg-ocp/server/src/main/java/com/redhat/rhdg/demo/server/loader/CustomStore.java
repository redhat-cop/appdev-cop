package com.redhat.rhdg.demo.server.loader;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.CompletionStage;

import org.infinispan.commons.configuration.ConfiguredBy;
import org.infinispan.commons.marshall.WrappedByteArray;
import org.infinispan.persistence.spi.InitializationContext;
import org.infinispan.persistence.spi.MarshallableEntry;
import org.infinispan.persistence.spi.MarshallableEntryFactory;
import org.infinispan.persistence.spi.NonBlockingStore;
import org.infinispan.protostream.ProtobufUtil;
import org.infinispan.protostream.SerializationContext;
import org.infinispan.util.concurrent.BlockingManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.redhat.rhdg.demo.model.ProtoInitializer;
import com.redhat.rhdg.demo.model.ProtoInitializerImpl;
import com.redhat.rhdg.demo.model.proto.ProtoKey;
import com.redhat.rhdg.demo.model.proto.ProtoValue;

@ConfiguredBy(CustomStoreConfiguration.class)
public class CustomStore<K, V> implements NonBlockingStore<K, V> {

	private SerializationContext serializationCtx;
	private MarshallableEntryFactory<K, V> entryFactory;
	private BlockingManager blockingManager;
	private Logger logger = LoggerFactory.getLogger(this.getClass());
	
	@Override
	public Set<NonBlockingStore.Characteristic> characteristics() {
		return new HashSet<Characteristic>(Arrays.asList(NonBlockingStore.Characteristic.READ_ONLY));
	}

	@Override
	public CompletionStage<Void> start(InitializationContext ctx) {
		return CompletableFuture.runAsync(() -> {
			this.serializationCtx = ProtobufUtil.newSerializationContext();
			ProtoInitializer initializer = new ProtoInitializerImpl();
			initializer.registerSchema(this.serializationCtx);
			initializer.registerMarshallers(this.serializationCtx);
			
			this.entryFactory = ctx.getMarshallableEntryFactory();
			this.blockingManager = ctx.getBlockingManager();
			return;
		});
	}

	@Override
	public CompletionStage<Void> stop() {
		return CompletableFuture.runAsync(() -> {});
	}

	@Override
	public CompletionStage<MarshallableEntry<K, V>> load(int segment, Object keyBytes) {
		return CompletableFuture.supplyAsync(() -> {
			try {
				logger.info("Loading value for key " + keyBytes.toString());
				ProtoKey key = ProtobufUtil.fromWrappedByteArray(serializationCtx, 
						((WrappedByteArray) keyBytes).getBytes());
				// generates a dummy value from the key, by just taking the key's hash
				ProtoValue value = new ProtoValue(key.hashCode() + "");
				byte[] valueBytes = ProtobufUtil.toWrappedByteArray(serializationCtx, value);
				return entryFactory.create(keyBytes, valueBytes);
			} catch (Exception e) {
				throw new CompletionException("Marshalling failed for key " + keyBytes.toString(), e);
			}
		}, blockingManager.asExecutor(this.getClass().getName()));
	}

	@Override
	public CompletionStage<Void> write(int segment, MarshallableEntry<? extends K, ? extends V> entry) {
		return CompletableFuture.failedStage(new UnsupportedOperationException("CustomStore is READ_ONLY"));
	}

	@Override
	public CompletionStage<Boolean> delete(int segment, Object key) {
		return CompletableFuture.failedStage(new UnsupportedOperationException("CustomStore is READ_ONLY"));
	}

	@Override
	public CompletionStage<Void> clear() {
		return CompletableFuture.failedStage(new UnsupportedOperationException("CustomStore is READ_ONLY"));
	}

}
